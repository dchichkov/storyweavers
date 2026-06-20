#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/splinter_bad_ending_cautionary_slice_of_life.py
================================================================================

A standalone story world about a small slice-of-life mishap: a child ignores a
simple warning, gets a splinter from rough wood, and the day turns into a
cautionary bad ending. The domain stays tiny and physical: a bench, a porch,
a wooden crate, a needle, a bandage, and a careful grown-up response that
comes too late to fully undo the trouble.

This world models state over time instead of swapping nouns into a frozen text.
Characters have meters and memes; the story is emitted from what changed.
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
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
class Setting:
    id: str
    place: str
    detail: str
    indoor: bool = False


@dataclass
class Hazard:
    id: str
    label: str
    source: str
    scratchy: bool
    bites: bool
    where: str
    tag: str


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


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
    child = world.get("child")
    for e in world.entities.values():
        if e.meters["splinter"] < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["worry"] += 1
        child.meters["pain"] += 1
        out.append("__pain__")
    return out


def _r_infection(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["splinter"] < THRESHOLD:
        return out
    if child.meters["pain"] < THRESHOLD:
        return out
    sig = ("infection",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["swelling"] += 1
    child.memes["fear"] += 1
    out.append("__infection__")
    return out


def _r_late_help(world: World) -> list[str]:
    out: list[str] = []
    adult = world.get("adult")
    child = world.get("child")
    if not adult.memes["noticed"] >= THRESHOLD:
        return out
    if child.meters["splinter"] < THRESHOLD:
        return out
    sig = ("help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult.memes["concern"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [
    Rule("spread", "physical", _r_spread),
    Rule("infection", "physical", _r_infection),
    Rule("late_help", "social", _r_late_help),
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


def hazard_risk(hazard: Hazard) -> bool:
    return hazard.scratchy and hazard.bites


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def injury_severity(delay: int) -> int:
    return 1 + delay


def contained(response: Response, delay: int) -> bool:
    return response.power >= injury_severity(delay)


def predict_harm(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _do_bad_choice(sim, sim.get(hazard_id), narrate=False)
    return {
        "pain": sim.get("child").meters["pain"],
        "swelling": sim.get("child").meters["swelling"],
    }


def _do_bad_choice(world: World, hazard_ent: Entity, narrate: bool = True) -> None:
    hazard_ent.meters["splinter"] += 1
    hazard_ent.meters["scraped"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    child.memes["calm"] += 1
    world.say(
        f"On an ordinary afternoon, {child.id} and {adult.id} were spending time "
        f"around {setting.place}. {setting.detail}"
    )
    world.say(
        f"{child.id} liked the small routines of the day: a snack, a quiet game, "
        f"and the warm light on the floor."
    )


def notice_rough_wood(world: World, child: Entity, hazard: Hazard) -> None:
    world.say(
        f"Near the old bench, {hazard.where} looked rough and dry. "
        f"{child.id} could see little bits of wood sticking up."
    )
    world.say(
        f'"That looks splintery," {child.id} muttered, and {child.pronoun()} '
        f"thought about leaving it alone."
    )


def tempt(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"But when a loose package rolled under the bench, {child.id} reached for it "
        f"anyway. The rough wood was right there."
    )
    world.say(
        f'"It will only take a second," {child.id} said, even though the wood felt '
        f"{'scratchy' if hazard.scratchy else 'smooth'} under {child.pronoun('possessive')} fingers."
    )


def warn(world: World, adult: Entity, child: Entity, hazard: Hazard) -> None:
    child.memes["warning"] += 1
    world.say(
        f'{adult.id} looked up from the doorway and said, "Careful. {hazard.label.capitalize()} can bite '
        f"your skin and leave a splinter.""
    )


def defy(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} ignored the warning and slid a hand across the wood anyway. '
        f'Just one quick touch.'
    )


def hurt(world: World, hazard: Hazard) -> None:
    _do_bad_choice(world, world.get("hazard"))
    world.say(
        f"A tiny splinter stuck in {world.get('child').pronoun('possessive')} skin. "
        f"It hurt more than {world.get('child').id} expected."
    )


def alarm(world: World, child: Entity, adult: Entity, hazard: Hazard) -> None:
    world.say(
        f'"Ow!" {child.id} yelped. {adult.id} hurried over at once.'
    )


def rescue(world: World, adult: Entity, response: Response) -> None:
    child = world.get("child")
    if response.id == "needle":
        child.meters["splinter"] = 0.0
    body = response.text
    world.say(f"{adult.label_word.capitalize()} sat beside {child.id} and {body}.")
    world.say(
        f"The splinter was out, but the finger still ached and looked angry."
    )


def bad_end(world: World, child: Entity, adult: Entity) -> None:
    world.say("The next day, the finger was red and swollen.")
    world.say(
        f"{adult.label_word.capitalize()} had to take {child.id} to a clinic, where "
        f"the nurse cleaned the sore spot and said it should have been handled sooner."
    )
    world.say(
        f"{child.id} watched the bandage wrap around {child.pronoun('possessive')} finger "
        f"and wished {child.pronoun()} had listened the first time."
    )


def lesson(world: World, child: Entity, adult: Entity, hazard: Hazard) -> None:
    world.say(
        f'"A splinter can seem small," {adult.id} said gently, '
        f'"but little injuries can turn into bigger problems if you ignore them."'
    )
    world.say(
        f'{child.id} nodded slowly and kept {child.pronoun("possessive")} hand tucked away.'
    )


def tell(setting: Setting, hazard: Hazard, response: Response,
         child_name: str = "Mina", child_type: str = "girl",
         adult_name: str = "Mom", adult_type: str = "mother",
         delay: int = 1) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_type, role="adult"))
    haz = world.add(Entity(id="hazard", type="thing", label=hazard.label, role="hazard"))

    child.memes["care"] = 1.0
    adult.memes["care"] = 2.0
    adult.memes["noticed"] = 1.0
    world.facts["delay"] = delay

    intro(world, child, adult, setting)
    notice_rough_wood(world, child, hazard)
    world.para()
    tempt(world, child, hazard)
    warn(world, adult, child, hazard)
    defy(world, child, hazard)

    world.para()
    hurt(world, hazard)
    alarm(world, child, adult, hazard)

    severity = injury_severity(delay)
    world.facts["severity"] = severity
    if contained(response, delay):
        rescue(world, adult, response)
        lesson(world, child, adult, hazard)
        world.say(
            f"By bedtime, the child was safe, but the day had become a reminder to "
            f"stop at the first sharp little warning."
        )
        outcome = "contained"
    else:
        world.say(
            f"{adult.label_word.capitalize()} tried to help, but the splinter had already "
            f"made the finger throb and throb."
        )
        bad_end(world, child, adult)
        world.say(
            f"From then on, {child.id} remembered the rough bench as something to avoid."
        )
        outcome = "bad"

    world.facts.update(
        child=child, adult=adult, hazard=hazard, response=response,
        outcome=outcome, splintered=True, warned=True, hurt=True,
    )
    return world


SETTINGS = {
    "porch": Setting("porch", "the front porch", "The porch boards were old and sun-faded.", False),
    "workshop": Setting("workshop", "the little workshop", "A small wooden stool sat beside a crate of nails.", True),
    "yard_bench": Setting("yard_bench", "the backyard bench", "The bench paint had peeled, leaving the wood rough.", False),
}

HAZARDS = {
    "bench_splinter": Hazard(
        "bench_splinter",
        "the bench",
        "rough wood",
        True,
        True,
        "the edge of the bench",
        "splinter",
    ),
    "crate_splinter": Hazard(
        "crate_splinter",
        "the crate",
        "a cracked crate lid",
        True,
        True,
        "the splintered crate edge",
        "splinter",
    ),
    "step_splinter": Hazard(
        "step_splinter",
        "the step",
        "a broken stair step",
        True,
        True,
        "the rough stair edge",
        "splinter",
    ),
}

RESPONSES = {
    "tweezers": Response(
        "tweezers",
        3,
        3,
        "used tweezers to pinch the splinter out carefully and cleaned the spot with soap and water",
        "used tweezers, but the splinter had gone in too deep",
        "used tweezers to remove the splinter and cleaned the skin",
    ),
    "needle": Response(
        "needle",
        2,
        2,
        "lifted the splinter out with a clean needle and then wrapped the finger in a small bandage",
        "tried a clean needle, but the finger was already too sore and hard to fix at home",
        "lifted the splinter out with a clean needle and wrapped it in a bandage",
    ),
    "ice": Response(
        "ice",
        1,
        1,
        "held a cold cloth on the finger and hoped the splinter would behave",
        "pressed a cold cloth on the finger, but it did not reach the splinter at all",
        "held a cold cloth on the finger",
    ),
}

NAMES = ["Mina", "Ivy", "Nora", "Lila", "June", "Eli", "Owen", "Noah"]
TRAITS = ["careful", "curious", "quiet", "thoughtful", "patient", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid, hazard in HAZARDS.items():
            if hazard_risk(hazard):
                combos.append((sid, hid))
    return combos


@dataclass
class StoryParams:
    setting: str
    hazard: str
    response: str
    child: str
    child_type: str
    adult: str
    adult_type: str
    trait: str
    delay: int = 1
    seed: Optional[int] = None


KNOWLEDGE = {
    "splinter": [("What is a splinter?",
                  "A splinter is a tiny sharp piece of wood that can stick into your skin.")],
    "tweezers": [("What are tweezers for?",
                  "Tweezers are small tools that help pinch and pull out tiny things, like a splinter.")],
    "needle": [("Why should a grown-up use a needle carefully?",
                 "A needle is sharp, so a grown-up should handle it slowly and cleanly to avoid making an injury worse.")],
    "bandage": [("What does a bandage do?",
                 "A bandage covers a sore spot and helps keep it clean while it heals.")],
    "clinic": [("When should you go to a clinic?",
                 "You should go to a clinic when a small problem becomes painful, swollen, or hard to fix at home.")],
    "warning": [("Why should you listen to a warning?",
                 "Warnings help you stop before something small turns into a bigger problem.")],
}
KNOWLEDGE_ORDER = ["splinter", "warning", "tweezers", "needle", "bandage", "clinic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life cautionary story for a young child that includes the word "splinter".',
        f"Tell a small everyday story where {f['child'].id} ignores a warning about {f['hazard'].label} and gets hurt a little, then the day goes wrong.",
        f"Write a simple bad-ending story about rough wood, a small injury, and a lesson about listening to a grown-up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, hazard, response = f["child"], f["adult"], f["hazard"], f["response"]
    out = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {adult.id}, an ordinary child and a caring grown-up sharing a normal day.",
        ),
        QAItem(
            question="What warning did the grown-up give?",
            answer=f"{adult.id} warned {child.id} to be careful around {hazard.label} because rough wood can leave a splinter in the skin.",
        ),
        QAItem(
            question="What happened when the child ignored the warning?",
            answer=f"A tiny splinter went into {child.pronoun('possessive')} skin, and the finger started to hurt right away.",
        ),
    ]
    if f["outcome"] == "bad":
        out.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"It ended badly for a small everyday problem: the finger got red and swollen, "
                    f"and {child.id} had to go to a clinic. "
                    f"The ending shows that even a tiny splinter can become a bigger trouble if nobody listens early."
                ),
            )
        )
    else:
        out.append(
            QAItem(
                question="How did the grown-up help?",
                answer=(
                    f"{adult.id} removed the splinter with {response.id} and cleaned the spot. "
                    f"That helped the pain go down, even though the story still keeps its cautionary feeling."
                ),
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["hazard"].tag, "warning", world.facts["response"].id}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("porch", "bench_splinter", "tweezers", "Mina", "girl", "Mom", "mother", "careful", 1),
    StoryParams("yard_bench", "crate_splinter", "needle", "Eli", "boy", "Dad", "father", "curious", 2),
    StoryParams("workshop", "step_splinter", "ice", "Nora", "girl", "Mom", "mother", "thoughtful", 1),
]


def explain_rejection(hazard: Hazard) -> str:
    return f"(No story: {hazard.label} does not make a plausible splinter scene.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': sense={r.sense} < {SENSE_MIN}. Try: {better}.)"


def outcome_of(params: StoryParams) -> str:
    return "contained" if contained(RESPONSES[params.response], params.delay) else "bad"


ASP_RULES = r"""
hazard(H) :- scratchy(H), bites(H).
sensible(R) :- response(R), sense(R,S), min_sense(M), S >= M.
contained :- chosen_response(R), power(R,P), delay(D), severity(S), P >= S.
severity(1 + D) :- delay(D).
outcome(contained) :- contained.
outcome(bad) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.scratchy:
            lines.append(asp.fact("scratchy", hid))
        if h.bites:
            lines.append(asp.fact("bites", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("min_sense", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hazard/1."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generated story smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    cases = CURATED[:]
    for s in range(30):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            pass
    mismatch = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatch:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small splinter mishap, cautionary and slice-of-life."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-type", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late help comes")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.hazard and args.hazard not in HAZARDS:
        raise StoryError(explain_rejection(HAZARDS["bench_splinter"]))

    hazard = args.hazard or rng.choice(sorted(HAZARDS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    adult_type = args.adult_type or ("mother" if child_type == "girl" else "father")
    child = args.child or rng.choice(NAMES)
    adult = args.adult or ("Mom" if adult_type == "mother" else "Dad")
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    trait = rng.choice(TRAITS)
    return StoryParams(setting, hazard, response, child, child_type, adult, adult_type, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        HAZARDS[params.hazard],
        RESPONSES[params.response],
        params.child,
        params.child_type,
        params.adult,
        params.adult_type,
        params.delay,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show hazard/1.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(asp_valid_combos())} plausible hazard combos:\n")
        for (hid,) in asp_valid_combos():
            print(f"  {hid}")
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
            header = f"### {p.child} and {p.adult}: {p.hazard} -> {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
