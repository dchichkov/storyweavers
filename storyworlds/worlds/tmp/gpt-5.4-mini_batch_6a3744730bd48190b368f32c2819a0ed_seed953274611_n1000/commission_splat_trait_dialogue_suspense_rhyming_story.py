#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/commission_splat_trait_dialogue_suspense_rhyming_story.py
=========================================================================================

A tiny story world about a child taking a commission to make a gift, then a
paint splat creates suspense, dialogue helps solve the problem, and the ending
lands in a rhyming, cozy image.

The domain is deliberately small:
- a young maker receives a commission
- a trait like careful / clever / brave affects whether they panic or stay calm
- a splat event can happen if paint gets bumped
- a helper can rescue the work with a simple, sensible fix
- stories are rendered with light rhyme and dialogue

The script follows the Storyweavers world contract:
- typed entities with meters and memes
- world-state-driven prose
- three QA sets from world state
- inline ASP twin + Python reasonableness gate
- --verify checks parity and exercises story generation
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
    role: str = ""
    trait: str = ""
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
class Commission:
    id: str
    item: str
    phrase: str
    purpose: str
    rhyme_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Paint:
    id: str
    color: str
    label: str
    phrase: str
    splat_sound: str
    mess: str
    can_splat: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TraitProfile:
    id: str
    label: str
    meter_boost: int
    meme_boost: int
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_splat(world: World) -> list[str]:
    out: list[str] = []
    painter = world.get("maker")
    if painter.meters["paint"] < THRESHOLD:
        return out
    sig = ("splat", painter.id)
    if sig in world.fired:
        return out
    if world.get("work").meters["steady"] < THRESHOLD:
        world.fired.add(sig)
        painter.meters["mess"] += 1
        world.get("work").meters["stained"] += 1
        world.get("work").memes["risk"] += 1
        out.append("__splat__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("work").meters["stained"] < THRESHOLD:
        return out
    sig = ("worry", 1)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("maker").memes["worry"] += 1
    world.get("helper").memes["alert"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("splat", "physical", _r_splat), Rule("worry", "social", _r_worry)]


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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def hazard_at_risk(commission: Commission, paint: Paint) -> bool:
    return commission.can_splat and paint.can_splat


def can_rescue(fix: Fix, delay: int) -> bool:
    return fix.power >= 1 + delay


def reasonableness_gate(commission: Commission, paint: Paint) -> bool:
    return hazard_at_risk(commission, paint)


def calm_trait(name: str) -> int:
    return 2 if name in {"careful", "steady", "patient"} else 1


def predict_splat(world: World) -> dict:
    sim = world.copy()
    _do_paint(sim, narrate=False)
    return {"stained": sim.get("work").meters["stained"] >= THRESHOLD, "risk": sim.get("helper").memes["alert"]}


def _do_paint(world: World, narrate: bool = True) -> None:
    world.get("maker").meters["paint"] += 1
    propagate(world, narrate=narrate)


def _add_rhyme(base: str) -> str:
    return base


def intro(world: World, maker: Entity, helper: Entity, commission: Commission, trait: TraitProfile) -> None:
    maker.memes["pride"] += trait.meme_boost
    world.say(
        f"{maker.id} got a commission with a cheerful tune: {commission.phrase}. "
        f"{helper.id} came by to see the scene, and the room felt bright and clean."
    )
    world.say(
        f'"{commission.purpose}," said {maker.id}. "{commission.item} must be neat!" '
        f'"{trait.helps}," said {helper.id}, "and then the gift will be complete."'
    )


def suspense(world: World, maker: Entity, helper: Entity, paint: Paint, commission: Commission) -> None:
    maker.memes["focus"] += 1
    helper.memes["alert"] += 1
    world.say(
        f"The brush went swish, the cup sat high; the wet paint glowed like evening sky. "
        f"But then the table gave a shake, and everyone felt a little quake."
    )
    world.say(
        f'"Careful," said {helper.id}, "that jar may tip." "{maker.id}," said the maker, "I have a grip."'
    )


def cause_splat(world: World, maker: Entity, paint: Paint, commission: Commission) -> None:
    _do_paint(world)
    world.say(
        f"{paint.splat_sound} went the paint! A sudden splat! "
        f"A drip ran down the {commission.item}, imagine that."
    )


def alarm(world: World, helper: Entity, maker: Entity, commission: Commission) -> None:
    world.say(
        f'"Oh no!" cried {helper.id}. "{maker.id}, look there! The {commission.item} got a messy smear!"'
    )
    world.say(f'"I see it," said {maker.id}, "but I can fix it fair."')


def rescue(world: World, helper: Entity, fix: Fix, commission: Commission) -> None:
    world.get("work").meters["stained"] = 0.0
    world.get("maker").meters["mess"] = 0.0
    world.say(
        f"{helper.id} said, \"{fix.text}.\" The maker nodded, calm and bright, "
        f"and wiped the splat away just right."
    )
    world.say(
        f"The colors came back bold and true; the {commission.item} shone like morning dew."
    )


def rescue_fail(world: World, helper: Entity, fix: Fix, commission: Commission) -> None:
    world.get("work").meters["stained"] += 1
    world.say(
        f"{helper.id} tried to help, but {fix.fail}. The stain stayed on in a stubborn line."
    )
    world.say(
        f"So they slowed down, breathed, and made a plan, to finish safely, as they can."
    )


def ending(world: World, maker: Entity, helper: Entity, commission: Commission, trait: TraitProfile, fixed: bool) -> None:
    if fixed:
        world.say(
            f"At last the commission glowed; the gift was done, the good deed showed. "
            f"{maker.id} smiled wide, {helper.id} near by, and the room felt light beneath the sky."
        )
    else:
        world.say(
            f"At last the work still took more time, but patience turned the mess to rhyme. "
            f"{maker.id} kept going, step by step, till every line was neat and kept."
        )
    world.say(
        f"Their {trait.label} trait had helped them through; the splat was gone, the night felt new."
    )


def tell(commission: Commission, paint: Paint, trait: TraitProfile, fix: Fix, delay: int = 0,
         maker_name: str = "Mina", maker_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy") -> World:
    world = World()
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    work = world.add(Entity(id="work", type="thing", label=commission.item))
    world.add(Entity(id="paint", type="thing", label=paint.label))

    maker.meters["paint"] = 0
    helper.memes["alert"] = 0
    work.meters["stained"] = 0
    world.facts["delay"] = delay

    intro(world, maker, helper, commission, trait)
    world.para()
    suspense(world, maker, helper, paint, commission)
    if reasonableness_gate(commission, paint):
        cause_splat(world, maker, paint, commission)
        alarm(world, helper, maker, commission)
        world.para()
        if can_rescue(fix, delay):
            rescue(world, helper, fix, commission)
            ending(world, maker, helper, commission, trait, True)
            outcome = "fixed"
        else:
            rescue_fail(world, helper, fix, commission)
            ending(world, maker, helper, commission, trait, False)
            outcome = "delayed"
    else:
        world.say("No splat came at all, so they painted with care and small delight.")
        ending(world, maker, helper, commission, trait, True)
        outcome = "averted"

    world.facts.update(
        maker=maker, helper=helper, commission=commission, paint=paint, trait=trait,
        fix=fix, outcome=outcome, stained=world.get("work").meters["stained"] >= THRESHOLD
    )
    return world


COMMISSIONS = {
    "card": Commission(id="card", item="card", phrase="a birthday card commission", purpose="It is for a friend", rhyme_word="spark", tags={"card", "commission"}),
    "poster": Commission(id="poster", item="poster", phrase="a sunny poster commission", purpose="It is for a shop window", rhyme_word="glow", tags={"poster", "commission"}),
    "banner": Commission(id="banner", item="banner", phrase="a welcome banner commission", purpose="It is for the class hall", rhyme_word="cheer", tags={"banner", "commission"}),
}

PAINTS = {
    "red": Paint(id="red", color="red", label="red paint", phrase="a pot of red paint", splat_sound="Splat!", mess="stain", can_splat=True, tags={"paint", "splat"}),
    "blue": Paint(id="blue", color="blue", label="blue paint", phrase="a pot of blue paint", splat_sound="Splish-splat!", mess="stain", can_splat=True, tags={"paint", "splat"}),
    "gold": Paint(id="gold", color="gold", label="gold paint", phrase="a pot of gold paint", splat_sound="Plop-splat!", mess="stain", can_splat=True, tags={"paint", "splat"}),
}

TRAITS = {
    "careful": TraitProfile(id="careful", label="careful", meter_boost=1, meme_boost=2, helps="Careful hands keep it neat", tags={"trait"}),
    "clever": TraitProfile(id="clever", label="clever", meter_boost=1, meme_boost=1, helps="Clever minds can mend the scene", tags={"trait"}),
    "brave": TraitProfile(id="brave", label="brave", meter_boost=1, meme_boost=1, helps="Brave hearts keep trying, even when it bites", tags={"trait"}),
    "steady": TraitProfile(id="steady", label="steady", meter_boost=2, meme_boost=2, helps="Steady hands make the lines look right", tags={"trait"}),
}

FIXES = {
    "cloth": Fix(id="cloth", sense=3, power=2, text="grabbed a soft cloth and dabbed the splash away", fail="the cloth was too small for the whole big blot", qa_text="grabbed a soft cloth and dabbed the splash away", tags={"fix"}),
    "drying": Fix(id="drying", sense=2, power=1, text="set the page aside to dry, then touched up the edge", fail="the paint still slid before it could dry", qa_text="set the page aside to dry and touched up the edge", tags={"fix"}),
    "redo": Fix(id="redo", sense=3, power=2, text="carefully painted the splat into a star and made it new", fail="the redo took too long and the blot stayed bold", qa_text="painted the splat into a star and made it new", tags={"fix"}),
    "water_wipe": Fix(id="water_wipe", sense=1, power=0, text="used a wet hand to wipe, which only spread the stain", fail="used a wet hand to wipe, which only spread the stain", qa_text="used a wet hand to wipe", tags={"fix"}),
}

NAMES_BOY = ["Ben", "Noah", "Theo", "Finn", "Eli"]
NAMES_GIRL = ["Mina", "Ivy", "Luna", "Nora", "Zoe"]


@dataclass
class StoryParams:
    commission: str
    paint: str
    trait: str
    fix: str
    maker_name: str
    maker_gender: str
    helper_name: str
    helper_gender: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for cid in COMMISSIONS:
        for pid in PAINTS:
            for tid in TRAITS:
                if reasonableness_gate(COMMISSIONS[cid], PAINTS[pid]):
                    out.append((cid, pid, tid))
    return out


def explain_rejection(commission: Commission, paint: Paint) -> str:
    if not reasonableness_gate(commission, paint):
        return "(No story: that paint cannot make the kind of splat this tale needs.)"
    return "(No story: invalid combination.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    return f"(Refusing fix '{fid}': it is too weak to matter in a suspense story.)" if fix.sense < SENSE_MIN else "(OK)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: commission, splat, trait, dialogue, suspense, rhyme.")
    ap.add_argument("--commission", choices=COMMISSIONS)
    ap.add_argument("--paint", choices=PAINTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--maker-name")
    ap.add_argument("--maker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    combos = [(c, p, t) for (c, p, t) in valid_combos()
              if (args.commission is None or c == args.commission)
              and (args.paint is None or p == args.paint)
              and (args.trait is None or t == args.trait)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    commission, paint, trait = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(fid for fid, f in FIXES.items() if f.sense >= SENSE_MIN))
    maker_gender = args.maker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if maker_gender == "girl" else "girl")
    maker_name = args.maker_name or rng.choice(NAMES_GIRL if maker_gender == "girl" else NAMES_BOY)
    helper_name = args.helper_name or rng.choice(NAMES_BOY if helper_gender == "boy" else NAMES_GIRL)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        commission=commission, paint=paint, trait=trait, fix=fix,
        maker_name=maker_name, maker_gender=maker_gender,
        helper_name=helper_name, helper_gender=helper_gender,
        delay=delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, p, t = f["commission"], f["paint"], f["trait"]
    return [
        f'Write a rhyming story with dialogue about a {c.item} commission, a {p.color} splat, and the trait "{t.label}".',
        f"Tell a suspenseful story where {f['maker'].id} works on {c.phrase} and there is a {p.splat_sound} moment.",
        f'Write a child-friendly rhyme using the words commission, splat, and trait, with a helpful conversation and a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker, helper, commission, paint, fix = f["maker"], f["helper"], f["commission"], f["paint"], f["fix"]
    out = [
        QAItem(
            question="What was the commission?",
            answer=f"It was {commission.phrase}. The maker was trying to finish that special job for someone else, so the work mattered a lot."
        ),
        QAItem(
            question="What caused the suspense?",
            answer=f"The {paint.color} paint made a {paint.splat_sound.lower()} and splat onto the work. That made everyone worry for a moment because the gift might be ruined."
        ),
        QAItem(
            question="How did the helper respond?",
            answer=f"{helper.id} spoke up at once and helped calm the scene. The helper used a sensible fix instead of panicking, which kept the story moving toward a solution."
        ),
        QAItem(
            question="What trait helped most?",
            answer=f"The {f['trait'].label} trait helped the maker keep going. It made it easier to listen, breathe, and finish the commission after the surprise."
        ),
    ]
    if f["outcome"] == "fixed":
        out.append(QAItem(
            question="How did the story end?",
            answer=f"It ended happily because {fix.qa_text} and the commission was saved. The splat was gone, and the finished piece could be handed over with pride."
        ))
    elif f["outcome"] == "delayed":
        out.append(QAItem(
            question="How did the story end?",
            answer="It ended with a slower rescue. The first try was not enough, but the characters stayed calm and kept working until the piece was finished."
        ))
    else:
        out.append(QAItem(
            question="How did the story end?",
            answer="It ended without a real mess, so the maker finished the work neatly the first time. The suspense faded into a bright and peaceful final scene."
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["commission"].tags) | set(world.facts["paint"].tags) | set(world.facts["trait"].tags) | {"fix"}
    qa = []
    if "commission" in tags:
        qa.append(QAItem("What is a commission?", "A commission is a job someone asks you to make for them. It is often something special that should be done with care."))
    if "splat" in tags:
        qa.append(QAItem("What is a splat?", "A splat is a sudden messy spread of paint or liquid. It often means something has been spilled or bumped."))
    if "trait" in tags:
        qa.append(QAItem("What is a trait?", "A trait is a way someone often acts, like being careful or brave. Traits help shape how a character handles trouble."))
    if "fix" in tags:
        qa.append(QAItem("What does it mean to fix something?", "To fix something means to make it better after it goes wrong. In stories, a fix can be a tool, a plan, or a calm choice."))
    return qa


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.commission not in COMMISSIONS or params.paint not in PAINTS or params.trait not in TRAITS or params.fix not in FIXES:
        raise StoryError("(Invalid params.)")
    world = tell(
        COMMISSIONS[params.commission],
        PAINTS[params.paint],
        TRAITS[params.trait],
        FIXES[params.fix],
        delay=params.delay,
        maker_name=params.maker_name,
        maker_gender=params.maker_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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
hazard(C,P) :- commission(C), paint(P), can_splat(P).
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
outcome(fixed) :- chosen_fix(F), power(F,P), delay(D), P >= D+1.
outcome(delayed) :- chosen_fix(F), power(F,P), delay(D), P < D+1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in COMMISSIONS.items():
        lines.append(asp.fact("commission", cid))
        if "commission" in c.tags:
            lines.append(asp.fact("can_splat", cid))
    for pid, p in PAINTS.items():
        lines.append(asp.fact("paint", pid))
        lines.append(asp.fact("can_splat", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scen = asp.fact("chosen_fix", params.fix) + "\n" + asp.fact("delay", params.delay)
    model = asp.one_model(asp_program(scen, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def valid_response_ids() -> list[str]:
    return sorted(fid for fid, f in FIXES.items() if f.sense >= SENSE_MIN)


def asp_verify() -> int:
    rc = 0
    try:
        p = StoryParams(
            commission="card", paint="red", trait="careful", fix="cloth",
            maker_name="Mina", maker_gender="girl", helper_name="Ben", helper_gender="boy",
            delay=0, seed=0,
        )
        sample = generate(p)
        _ = sample.story
    except Exception as exc:
        print(f"FAILED: normal generation crashed: {exc}")
        return 1
    import asp
    if set(asp_valid_combos()) != {(c, p) for c, p, _ in valid_combos()}:
        rc = 1
        print("MISMATCH: ASP hazard gate differs from Python gate.")
    if set(asp_sensible()) != set(valid_response_ids()):
        rc = 1
        print("MISMATCH: ASP sensible fixes differ from Python gate.")
    cases = [
        StoryParams(commission="banner", paint="blue", trait="steady", fix="cloth",
                    maker_name="Ava", maker_gender="girl", helper_name="Theo", helper_gender="boy", delay=0, seed=1),
        StoryParams(commission="poster", paint="gold", trait="clever", fix="redo",
                    maker_name="Ivy", maker_gender="girl", helper_name="Noah", helper_gender="boy", delay=2, seed=2),
    ]
    for case in cases:
        if asp_outcome(case) not in {"fixed", "delayed"}:
            rc = 1
            print("MISMATCH: ASP outcome failed.")
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def explain_response(fid: str) -> str:
    fix = FIXES[fid]
    return f"(Refusing fix '{fid}': it is below the common-sense floor.)" if fix.sense < SENSE_MIN else "(OK)"


def CURATED() -> list[StoryParams]:
    return [
        StoryParams(commission="card", paint="red", trait="careful", fix="cloth", maker_name="Mina", maker_gender="girl", helper_name="Ben", helper_gender="boy", delay=0, seed=1),
        StoryParams(commission="poster", paint="blue", trait="clever", fix="redo", maker_name="Ivy", maker_gender="girl", helper_name="Noah", helper_gender="boy", delay=1, seed=2),
        StoryParams(commission="banner", paint="gold", trait="steady", fix="drying", maker_name="Luna", maker_gender="girl", helper_name="Theo", helper_gender="boy", delay=2, seed=3),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show hazard/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible fixes:", ", ".join(asp_sensible()))
        print()
        for c, p in asp_valid_combos():
            print(f"{c} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED()]
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
        if args.all:
            p = sample.params
            header = f"### {p.maker_name}: {p.commission} with {p.paint} ({p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
