#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/payment_pharaoh_lesson_humor_sound_effects_superhero.py
=======================================================================================

A tiny superhero storyworld about a kid superhero helping a museum make a
missing payment to a playful pharaoh exhibit, while a lesson about responsibility
lands with humor and sound effects.

This world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- three Q&A sets grounded in the simulated world
- an inline ASP twin for parity checks

The story premise:
A child superhero sees a payment problem at a museum gift shop. A goofy mummy
mix-up and a dramatic "KA-POW!" moment lead to a lesson about paying on time,
with a pharaoh statue, a helpful adult, and a safe humorous ending.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/payment_pharaoh_lesson_humor_sound_effects_superhero.py
    python storyworlds/worlds/gpt-5.4-mini/payment_pharaoh_lesson_humor_sound_effects_superhero.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/payment_pharaoh_lesson_humor_sound_effects_superhero.py --verify
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
HUMOR_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    vibe: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    label: str
    demand: str
    sound: str
    difficulty: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    label: str
    action: str
    sound: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_stress(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["overdue"] < THRESHOLD:
            continue
        sig = ("stress", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__stress__")
    return out


def _r_lesson(world: World) -> list[str]:
    out = []
    kid = world.entities.get("kid")
    guide = world.entities.get("guide")
    if not kid or not guide:
        return out
    if kid.meters["helped"] >= THRESHOLD and guide.memes["lesson"] < THRESHOLD:
        sig = ("lesson", kid.id)
        if sig not in world.fired:
            world.fired.add(sig)
            guide.memes["lesson"] += 1
            out.append("__lesson__")
    return out


CAUSAL_RULES = [Rule("stress", _r_stress), Rule("lesson", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def problem_at_risk(problem: Problem, setting: Setting) -> bool:
    return "payment" in problem.tags and "museum" in setting.tags


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.power >= HUMOR_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            if problem_at_risk(PROBLEMS[p], SETTINGS[s]):
                combos.append((s, p))
    return combos


def reasonableness(problem: Problem, setting: Setting) -> str:
    if not problem_at_risk(problem, setting):
        return "(No story: that problem does not fit this setting well enough for a payment lesson.)"
    return ""


def predict_due(world: World, fix_id: str) -> dict:
    sim = world.copy()
    _do_fix(sim, sim.get("kid"), FIXES[fix_id], narrate=False)
    return {"solved": sim.get("kid").meters["helped"] >= THRESHOLD}


def _do_problem(world: World, kid: Entity, problem: Problem, narrate: bool = True) -> None:
    kid.meters["overdue"] += 1
    kid.memes["embarrassment"] += 1
    propagate(world, narrate=narrate)


def _do_fix(world: World, kid: Entity, fix: Fix, narrate: bool = True) -> None:
    kid.meters["helped"] += 1
    kid.memes["hope"] += 1
    world.say(fix.sound + " " + fix.action + "!")
    propagate(world, narrate=narrate)


def opening(world: World, kid: Entity, guide: Entity, setting: Setting, problem: Problem) -> None:
    world.say(f"At {setting.place}, {kid.id} wore a tiny cape and a huge grin.")
    world.say(f"{guide.id} pointed at the exhibit and said, '{setting.vibe}.'")
    world.say(f"Behind the glass, the {problem.label} looked dramatic and a little silly.")


def trouble(world: World, kid: Entity, guide: Entity, problem: Problem, pharaoh: Entity) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"Then came a loud {problem.sound}! {kid.id} noticed the {problem.demand} "
        f"wasn't ready, and the pharaoh statue seemed to frown in surprise."
    )
    world.say(
        f'"I can fix this!" {kid.id} said, but {guide.id} held up a calm hand. '
        f'"First we look, then we act," {guide.id} said.'
    )
    world.say(f"The pharaoh blinked under the museum lights like a royal grump in a bow tie.")


def warning(world: World, kid: Entity, guide: Entity, problem: Problem) -> None:
    world.say(
        f"{guide.id} explained that a missed {problem.label} could turn the room "
        f"into a worry parade. That was the lesson hidden in the fuss."
    )


def rescue(world: World, kid: Entity, guide: Entity, fix: Fix) -> None:
    world.say(
        f"With a cheerful {fix.sound}, {kid.id} used {fix.action}, and the payment issue "
        f"stopped being a problem."
    )
    world.say(
        f"{guide.id} laughed and said the best superheroes do not just boom and zoom; "
        f"they also finish the job."
    )


def ending(world: World, kid: Entity, guide: Entity, pharaoh: Entity, fix: Fix) -> None:
    world.say(
        f"At the end, the {pharaoh.label_word} gave a funny little nod, as if to say "
        f"'nice work,' and {kid.id} felt proud."
    )
    world.say(
        f"The lesson was simple: when payment gets messy, stay calm, ask for help, "
        f"and use the right fix."
    )


def joke_tag(world: World, problem: Problem) -> None:
    world.say(
        f"{problem.sound}! {problem.sound}! Even the vending machine seemed to chuckle."
    )


def tell(setting: Setting, problem: Problem, fix: Fix, kid_name: str = "Zippy",
         kid_type: str = "boy", guide_name: str = "Captain Penny",
         guide_type: str = "woman") -> World:
    world = World(setting)
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_type, role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="mentor"))
    pharaoh = world.add(Entity(id="Pharaoh", kind="character", type="man", label="pharaoh statue"))
    world.add(Entity(id="ledger", type="thing", label="ledger"))
    opening(world, kid, guide, setting, problem)
    world.para()
    trouble(world, kid, guide, problem, pharaoh)
    warning(world, kid, guide, problem)
    joke_tag(world, problem)
    _do_problem(world, kid, problem)
    world.para()
    rescue(world, kid, guide, fix)
    ending(world, kid, guide, pharaoh, fix)
    world.facts.update(setting=setting, problem=problem, fix=fix, kid=kid, guide=guide, pharaoh=pharaoh)
    return world


SETTINGS = {
    "museum": Setting(id="museum", place="the museum lobby", vibe="The lobby gleamed like a superhero headquarters", tags={"museum", "hero"}),
    "bazaar": Setting(id="bazaar", place="the sunny bazaar", vibe="The market buzzed like a parade of capes", tags={"market", "hero"}),
    "harbor": Setting(id="harbor", place="the harbor office", vibe="The harbor office hummed like a busy command center", tags={"office", "hero"}),
}

PROBLEMS = {
    "ticket": Problem(id="ticket", label="ticket payment", demand="payment", sound="KER-CHING", difficulty=1, tags={"payment", "museum"}),
    "bill": Problem(id="bill", label="gift-shop bill", demand="payment", sound="BIP-BIP", difficulty=1, tags={"payment", "museum"}),
    "entry": Problem(id="entry", label="entry fee", demand="payment", sound="DING-DONG", difficulty=1, tags={"payment", "museum"}),
}

FIXES = {
    "card": Fix(id="card", label="card tap", action="tap the card reader", sound="ZIP-ZAP", power=2, tags={"payment"}),
    "coins": Fix(id="coins", label="coin pouch", action="count the coins carefully", sound="CLINK-CLINK", power=2, tags={"payment"}),
    "help": Fix(id="help", label="help desk", action="call the front desk for help", sound="RING-RING", power=3, tags={"payment"}),
}

HERO_NAMES = ["Zippy", "Nova", "Spark", "Milo", "Pip"]
GUIDE_NAMES = ["Captain Penny", "Aunt Ada", "Dr. Zoom", "Ms. Comet"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    kid: str
    kid_type: str
    guide: str
    guide_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a child that includes the words "payment", "pharaoh", and "lesson".',
        f"Tell a funny superhero story where {f['kid'].id} helps with a {f['problem'].label} near a pharaoh statue.",
        f"Write a child-friendly comic-style story with sound effects and a lesson about paying on time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, guide, problem, fix = f["kid"], f["guide"], f["problem"], f["fix"]
    return [
        ("Who is the story about?",
         f"It is about {kid.id}, a small superhero, and {guide.id}, who helps guide the rescue."),
        ("What went wrong?",
         f"The {problem.label} was not ready, so the museum had a payment problem. That made everyone pause before the superhero move."),
        ("How was it fixed?",
         f"They used {fix.action}, and the problem stopped. The fix was calm, useful, and much better than panicking."),
        ("What lesson did they learn?",
         f"They learned to stay calm, ask for help, and finish the payment the right way. That lesson came after the funny noise and the brief worry."),
        ("How did the pharaoh react?",
         f"The pharaoh statue looked grumpy for a moment, then nodded at the end. It was a funny ending image, not a scary one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pharaoh?",
         "A pharaoh was an ancient Egyptian ruler. In stories, a pharaoh statue can add a grand and funny feeling."),
        ("What is a payment?",
         "A payment is money or another agreed way to pay for something. It helps a person or shop say the deal is finished."),
        ("What is a lesson?",
         "A lesson is something you learn that helps you do better next time. In a story, it can be the helpful idea at the end."),
        ("Why do superheroes sometimes make sound effects?",
         "Sound effects make the action feel lively and funny. They help a story sound big, quick, and exciting."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="museum", problem="ticket", fix="help", kid="Zippy", kid_type="boy", guide="Captain Penny", guide_type="woman"),
    StoryParams(setting="museum", problem="bill", fix="card", kid="Nova", kid_type="girl", guide="Dr. Zoom", guide_type="man"),
    StoryParams(setting="museum", problem="entry", fix="coins", kid="Spark", kid_type="boy", guide="Aunt Ada", guide_type="woman"),
]


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.problem in PROBLEMS and params.fix in FIXES


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, t))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("humor_min", HUMOR_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_related(S,P) :- setting(S), problem(P), problem_tag(P, payment).
good_fix(F) :- fix(F), power(F, P), humor_min(M), P >= M.
valid(S,P,F) :- reasonably_related(S,P), good_fix(F).
"""


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, fix=None, kid=None, kid_type=None, guide=None, guide_type=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero payment lesson storyworld with humor and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--kid")
    ap.add_argument("--kid-type", choices=["boy", "girl"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-type", choices=["man", "woman"])
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
    if args.setting and args.problem and not problem_at_risk(PROBLEMS[args.problem], SETTINGS[args.setting]):
        raise StoryError(reasonableness(PROBLEMS[args.problem], SETTINGS[args.setting]))
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    if not problem_at_risk(PROBLEMS[problem], SETTINGS[setting]):
        raise StoryError(reasonableness(PROBLEMS[problem], SETTINGS[setting]))
    kid_type = args.kid_type or rng.choice(["boy", "girl"])
    guide_type = args.guide_type or rng.choice(["man", "woman"])
    kid = args.kid or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    return StoryParams(setting=setting, problem=problem, fix=fix, kid=kid, kid_type=kid_type, guide=guide, guide_type=guide_type)


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid story params.")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix], params.kid, params.kid_type, params.guide, params.guide_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
