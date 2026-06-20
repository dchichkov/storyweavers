#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/conjunctivitis_shopping_mall_mystery_to_solve_whodunit.py
==========================================================================================

A standalone storyworld for a small whodunit set in a shopping mall.

Premise
-------
A child starts with a baffling red, itchy eye after a day at the mall. The child
and a grown-up follow clues through the mall, rule out innocent possibilities,
and solve the mystery by tracing the irritation to a shared makeup tester. The
ending proves the mystery was solved and the child got the right care.

This world keeps the story child-facing, concrete, and state-driven:
- typed entities with physical meters and emotional memes
- a small causal model for clues, symptoms, and solving the whodunit
- a reasonableness gate that only allows plausible cases
- a Python/ASP twin for parity checks
- three Q&A sets grounded in the simulated world

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/conjunctivitis_shopping_mall_mystery_to_solve_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/conjunctivitis_shopping_mall_mystery_to_solve_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/conjunctivitis_shopping_mall_mystery_to_solve_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/conjunctivitis_shopping_mall_mystery_to_solve_whodunit.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
class MallSetting:
    id: str
    place: str
    cue: str


@dataclass
class Suspect:
    id: str
    label: str
    action: str
    clue: str
    innocent: bool = False


@dataclass
class Culprit:
    id: str
    label: str
    source: str
    evidence: str
    spreads_irritation: bool = True


@dataclass
class Remedy:
    id: str
    label: str
    text: str
    explanation: str


class World:
    def __init__(self, setting: MallSetting) -> None:
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


def _r_symptoms(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    if kid.meters["exposure"] < THRESHOLD or kid.meters["red_eye"] >= THRESHOLD:
        return out
    sig = ("symptoms", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.meters["red_eye"] += 1
    kid.meters["itch"] += 1
    kid.memes["worry"] += 1
    out.append("__symptoms__")
    return out


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    if world.get("kid").meters["red_eye"] < THRESHOLD:
        return out
    sig = ("spread", "clinic")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("mystery").meters["oddness"] += 1
    return out


CAUSAL_RULES = [
    Rule("symptoms", "physical", _r_symptoms),
    Rule("spread", "physical", _r_spread),
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


def risky_exposure(culprit: Culprit, setting: MallSetting) -> bool:
    return culprit.spreads_irritation and "mall" in setting.id


def correct_remedy(remedy: Remedy) -> bool:
    return remedy.id in {"wash_hands", "visit_doctor"}


def predict_case(world: World, culprit_id: str) -> dict:
    sim = world.copy()
    culprit = sim.get(culprit_id)
    sim.get("kid").meters["exposure"] += 1
    propagate(sim, narrate=False)
    return {"red_eye": sim.get("kid").meters["red_eye"], "oddness": sim.get("mystery").meters["oddness"]}


def touch(world: World, culprit: Culprit) -> None:
    world.get("kid").meters["exposure"] += 1
    world.facts["source"] = culprit.id
    world.get("kid").memes["uneasy"] += 1
    world.say(
        f"At the {world.setting.place}, {world.get('kid').id} noticed something wrong. "
        f"One eye felt itchy, and the other stayed normal. It was odd enough to start a mystery."
    )
    propagate(world, narrate=False)


def clue(world: World, suspect: Suspect, ruled_out: bool = False) -> None:
    if ruled_out:
        world.say(
            f"They looked at {suspect.label}, but that clue did not fit. "
            f"{suspect.clue} was innocent, so it could not explain the red eye."
        )
    else:
        world.say(
            f"They checked {suspect.label} and saw a clue: {suspect.clue}. "
            f"That made the mystery feel smaller."
        )


def solve(world: World, culprit: Culprit, remedy: Remedy, helper: Entity) -> None:
    kid = world.get("kid")
    helper.memes["confidence"] += 1
    kid.memes["relief"] += 1
    kid.memes["fear"] = 0
    world.get("mystery").meters["oddness"] = 0
    world.say(
        f"{helper.id} followed the clues past the food court, past the bright toy store, "
        f"and into the small beauty shop. There, on the counter, was the real answer: "
        f"{culprit.evidence}."
    )
    world.say(
        f'That was the culprit. The shared tester had spread the trouble, and the word was '
        f'"conjunctivitis," the kind of eye problem that can pass from hands or shared things.'
    )
    world.say(
        f"{helper.id} washed {kid.pronoun('possessive')} hands, kept {kid.pronoun('possessive')} "
        f"eyes clean, and took {kid.id} to a doctor. {remedy.text}."
    )
    world.say(
        f"By the end, the red eye was no longer a mystery. {kid.id} blinked carefully, "
        f"held {kid.pronoun('possessive')} head high, and left the mall knowing what had caused it."
    )


def tell(setting: MallSetting, culprit: Culprit, remedy: Remedy, hero: str = "Mina",
         hero_gender: str = "girl", helper: str = "Mom", helper_gender: str = "woman") -> World:
    world = World(setting)
    kid = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    adult = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    mystery = world.add(Entity(id="mystery", type="thing", label="the mystery"))
    world.add(Entity(id="culprit", type="thing", label=culprit.label))
    touch(world, culprit)
    world.para()
    world.say(
        f"{helper} frowned, but not at {hero}. In a whodunit, a careful grown-up first looks for clues."
    )
    world.say(
        f"They asked what had happened near the fountain, the arcade, and the makeup kiosk. "
        f"Each place had a different clue, but not every clue was the answer."
    )
    suspects = [
        Suspect("fountain", "the fountain splash", "water", "It could make a sleeve wet, but not a red eye.", innocent=True),
        Suspect("arcade", "the arcade glow", "lights", "Bright lights can sting, yet they do not spread conjunctivitis.", innocent=True),
        Suspect("tester", "the makeup tester", "shared mascara", "It was used by many hands and sat right at eye level."),
    ]
    clue(world, suspects[0], ruled_out=True)
    clue(world, suspects[1], ruled_out=True)
    clue(world, suspects[2], ruled_out=False)
    world.para()
    solve(world, culprit, remedy, adult)
    world.facts.update(
        kid=kid, adult=adult, setting=setting, culprit=culprit, remedy=remedy,
        mystery=mystery, outcome="solved", source=culprit.id,
        exposure=kid.meters["exposure"] >= THRESHOLD,
        red_eye=kid.meters["red_eye"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "mall": MallSetting("mall", "shopping mall", "bright stores and busy walkways"),
}

CULPRITS = {
    "tester": Culprit("tester", "makeup tester", "shared mascara", "the same mascara wand had been used again and again"),
    "towel": Culprit("towel", "borrowed towel", "dirty towel", "the towel had been passed from hand to hand", spreads_irritation=False),
    "hand": Culprit("hand", "unwashed hand", "eye rub", "a hand had rubbed the eye after touching a shared surface"),
}

REMEDIES = {
    "wash_hands": Remedy("wash_hands", "wash hands", "They washed up and used clean tissue", "washing hands can keep germs from spreading"),
    "visit_doctor": Remedy("visit_doctor", "visit a doctor", "A doctor checked the eye and gave the right care", "a doctor can tell which eye problem it is"),
    "ignore": Remedy("ignore", "ignore it", "They waited and hoped it would disappear", "that would not be a sensible plan"),
}

NAMES = ["Mina", "Lily", "Noah", "Eli", "Ava", "Maya", "Theo", "Zoe"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CULPRITS.values():
            for r in REMEDIES.values():
                if risky_exposure(c, SETTINGS[s]) and correct_remedy(r):
                    combos.append((s, c.id, r.id))
    return combos


@dataclass
class StoryParams:
    setting: str
    culprit: str
    remedy: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "conjunctivitis": [("What is conjunctivitis?",
                       "Conjunctivitis is an eye infection or irritation that can make the eye red, watery, or itchy. It can spread when people touch their eyes and then touch things or other people.")],
    "eye": [("Why do eyes need care?",
             "Eyes help you see, so they need to stay clean and safe. If an eye is red or hurts, a doctor should check it.")],
    "hands": [("Why should you wash your hands?",
                "Washing your hands helps remove germs and dirt. Clean hands make it harder for sickness to spread.")],
    "mall": [("What is a shopping mall?",
               "A shopping mall is a place with many stores, hallways, and sometimes a food court where people shop and walk around.")],
    "tester": [("What is a tester in a store?",
                 "A tester is something customers can try before buying, like a makeup sample. Testers can be touched by many people, so they should be used carefully.")],
    "doctor": [("What does a doctor do?",
                "A doctor checks what is wrong and helps people feel better. Doctors can tell the difference between problems that look similar.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    culprit: Culprit = f["culprit"]
    return [
        f"Write a whodunit story for a young child set in a shopping mall that includes the word 'conjunctivitis' and ends with the mystery solved.",
        f"Tell a mystery to solve story where a child gets a red, itchy eye at the mall and the clue leads to {culprit.label}.",
        f"Write a gentle whodunit in a shopping mall where the answer is a shared item and a grown-up helps the child get the right care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid: Entity = f["kid"]
    adult: Entity = f["adult"]
    culprit: Culprit = f["culprit"]
    remedy: Remedy = f["remedy"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a whodunit mystery set in a shopping mall. The story follows clues until the cause of the eye problem is solved."
        ),
        QAItem(
            question=f"What happened to {kid.id}?",
            answer=f"{kid.id} got a red, itchy eye and the grown-up noticed something was wrong. The eye trouble became the mystery everyone needed to solve."
        ),
        QAItem(
            question="What was the real clue?",
            answer=f"The real clue was {culprit.evidence}. It showed that the makeup tester had been shared and could spread conjunctivitis."
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{adult.id} washed hands, kept things clean, and took {kid.id} to a doctor. {remedy.explanation.capitalize()}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"conjunctivitis", "eye", "hands", "mall", "tester", "doctor"}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            for q, a in items:
                out.append(QAItem(q, a))
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mall", "tester", "wash_hands", "Mina", "girl", "Mom", "woman"),
    StoryParams("mall", "hand", "visit_doctor", "Noah", "boy", "Dad", "man"),
]


def explain_rejection(culprit: Culprit, remedy: Remedy) -> str:
    if not risky_exposure(culprit, SETTINGS["mall"]):
        return "(No story: that clue would not realistically lead to conjunctivitis at the mall.)"
    if not correct_remedy(remedy):
        return "(No story: the ending needs a sensible care step, like washing hands or seeing a doctor.)"
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "solved"


ASP_RULES = r"""
risky(C, S) :- culprit(C), setting(S), spreads(C), mall(S).
good_remedy(R) :- remedy(R), sensible(R).
valid(S, C, R) :- risky(C, S), good_remedy(R).
outcome(solved) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("mall", sid))
    for cid, c in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        if c.spreads_irritation:
            lines.append(asp.fact("spreads", cid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        if correct_remedy(r):
            lines.append(asp.fact("sensible", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_remedy", params.remedy),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    cases = CURATED[:]
    for s in range(10):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            pass
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print("OK: ASP outcome parity passed.")
    else:
        rc = 1
        print(f"MISMATCH in outcome parity: {bad} cases.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit storyworld set in a shopping mall.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.culprit is None or c[1] == args.culprit)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, culprit, remedy = rng.choice(sorted(combos))
    hero = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(["Mom", "Dad", "Aunt June", "Grandma"])
    hero_gender = "girl" if hero in {"Mina", "Lily", "Ava", "Maya", "Zoe"} else "boy"
    helper_gender = "woman" if helper in {"Mom", "Aunt June", "Grandma"} else "man"
    return StoryParams(setting, culprit, remedy, hero, hero_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CULPRITS[params.culprit], REMEDIES[params.remedy],
                 params.hero, params.hero_gender, params.helper, params.helper_gender)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, c, r in combos:
            print(f"  {s:6} {c:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        print(sample_to_json(samples))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.setting}, {p.culprit}, {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def sample_to_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
