#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/southern_magic_tall_tale.py
============================================================

A standalone story world for a tiny southern tall tale with a touch of magic:
a child, a strange problem, a magical helper, and a big-easy ending image that
proves something changed for the better.

The domain is intentionally small and classical:
- a southern setting with one notable place
- a magical object that causes trouble
- one friendly helper or elder who knows a folk remedy
- a final magical turn that fixes the problem

The story stays child-facing and concrete. The state model drives the prose so
the ending is earned by world changes, not by a frozen paragraph swap.
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
MAGIC_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    weather: str
    tall_tale_image: str
    southern_phrase: str


@dataclass
class MagicCharm:
    id: str
    label: str
    sparkle: str
    trouble: str
    remedy_hint: str
    makes_magic: bool = True


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    spread: int
    cursed: bool = True


@dataclass
class Remedy:
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["glow"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["mischief"] += 1
        out.append("__spill__")
    return out


def _r_shimmer(world: World) -> list[str]:
    out: list[str] = []
    if world.get("problem").meters["haunted"] >= THRESHOLD and ("shimmer",) not in world.fired:
        world.fired.add(("shimmer",))
        world.get("child").memes["worry"] += 1
        out.append("__shimmer__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("shimmer", "social", _r_shimmer)]


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


def magic_at_risk(charm: MagicCharm, problem: Problem) -> bool:
    return charm.makes_magic and problem.cursed


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def fire_severity(problem: Problem, delay: int) -> int:
    return problem.spread + delay


def is_resolved(remedy: Remedy, problem: Problem, delay: int) -> bool:
    return remedy.power >= fire_severity(problem, delay)


def predict_trouble(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get("charm"), sim.get("problem"), narrate=False)
    return {
        "haunted": sim.get("problem").meters["haunted"] >= THRESHOLD,
        "mischief": sim.get("room").meters["mischief"],
    }


def _do_magic(world: World, charm: Entity, problem: Entity, narrate: bool = True) -> None:
    charm.meters["glow"] += 1
    problem.meters["haunted"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Down in the {setting.place}, where the {setting.southern_phrase} sat as easy as an old rocking chair, "
        f"{child.id} was out making a little trouble and a little fun."
    )
    world.say(
        f"The day was {setting.weather}, and the whole place looked as if it had been washed with honey-colored light."
    )
    world.say(
        f"{setting.tall_tale_image} {child.id} and {helper.id} had that sort of southern afternoon that seemed too big to fit inside one day."
    )


def need_magic(world: World, child: Entity, problem: Problem) -> None:
    world.say(
        f"But {problem.label} had gone all wrong. It kept {problem.risk}, and {child.id} knew plain old wishing would not be enough."
    )
    world.say(
        f'{child.id} peered at it and said, "I need a little magic, and I need it quick."'
    )


def tempt(world: World, child: Entity, charm: MagicCharm) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} spotted {charm.label}, and it sparkled {charm.sparkle} like a firefly with moonlight in its pocket."
    )
    world.say(
        f'"Well, butter my biscuits," {child.id} said. "If this here {charm.label} can shine, maybe it can fix my whole day."'
    )


def warn(world: World, helper: Entity, child: Entity, charm: MagicCharm, problem: Problem) -> None:
    pred = predict_trouble(world, "problem")
    helper.memes["care"] += 1
    world.facts["predicted_mischief"] = pred["mischief"]
    world.say(
        f'{helper.id} squinted at {charm.label} and said, "{child.id}, that shiny thing can stir up a heap of trouble. '
        f'Once it gets going, it can leave {problem.risk} and more."'
    )
    if pred["haunted"] >= THRESHOLD:
        world.say(f'{helper.id} tapped the porch rail and added, "Magic ain\'t a toy when it starts acting wild."')


def defy(world: World, child: Entity, charm: MagicCharm) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'But {child.id} grinned, held {charm.label} up to the light, and said, "I reckon I can handle one little sparkle."'
    )


def use_magic(world: World, child: Entity, charm: MagicCharm, problem: Problem) -> None:
    _do_magic(world, child, problem)
    world.say(
        f'{charm.sparkle.capitalize()}! {charm.label} flashed bright as a tin roof in July, and the trouble twitched and started to grow.'
    )
    world.say(
        f"The glow slipped off the charm and crawled into {problem.label}, making the whole thing feel spooky and hard to manage."
    )


def alarm(world: World, helper: Entity, child: Entity, problem: Problem) -> None:
    world.say(f'"{child.id}! Come quick!" {helper.id} shouted. "{problem.label} is acting up!"')


def rescue(world: World, helper: Entity, remedy: Remedy, problem: Problem, charm: MagicCharm) -> None:
    problem.meters["haunted"] = 0.0
    world.get("room").meters["mischief"] = 0.0
    body = remedy.text.replace("{problem}", problem.label)
    world.say(f"{helper.label_word.capitalize()} came hustling over and {body}.")
    world.say(
        f"The bad spell fell quiet, and the charm stopped glowing wild. What had been a noisy mess went still as a church pew at dusk."
    )


def lesson(world: World, helper: Entity, child: Entity, charm: MagicCharm) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    world.say("For a minute, nobody said a word.")
    world.say(
        f"Then {helper.id} laughed soft and hugged {child.id}. "
        f'"I am not cross that you got scared," {helper.pronoun()} said. '
        f'"I am glad you hollered for help. Remember: {charm.trouble}."'
    )


def magical_fix(world: World, helper: Entity, child: Entity, remedy: Remedy, setting: Setting) -> None:
    child.memes["joy"] += 1
    child.memes["hope"] += 1
    world.say(
        f"The next morning, {helper.id} had a surprise: {helper.pronoun().capitalize()} brought out {remedy.qa_text}."
    )
    world.say(
        f'"Now," {helper.pronoun()} smiled, "what does a child need on a big southern day like this?"'
    )
    world.say(
        f'{child.id} held up the new plan, and the {setting.place} looked bright again, like it had been ironed flat by sunshine.'
    )
    world.say(
        f"This time, {child.id} could keep the fun and leave the wild magic settled and safe."
    )


def no_fix(world: World, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{helper.label_word.capitalize()} tried the best {helper.pronoun('possessive')} could, but the trouble was too big and too quick."
    )
    world.say(
        f"The bad magic spread through the {problem.label}, and the whole scene ended in a loud, smoky fuss."
    )


def ending_image(world: World, child: Entity, setting: Setting, happy: bool) -> None:
    if happy:
        world.say(
            f"In the end, {child.id} sat on the porch with {setting.southern_phrase} drifting by, smiling at the quiet little sparkle that behaved itself at last."
        )
    else:
        world.say(
            f"In the end, the porch was empty, the air was smoky, and {child.id} learned that wild magic needs a grown-up hand."
        )


def tell(setting: Setting, charm: MagicCharm, problem: Problem, remedy: Remedy,
         child_name: str = "June", child_gender: str = "girl", helper_name: str = "Aunt May",
         helper_gender: str = "aunt", delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="charm", type="charm", label=charm.label))
    world.add(Entity(id="problem", type="problem", label=problem.label))

    opening(world, child, helper, setting)
    world.para()
    need_magic(world, child, problem)
    tempt(world, child, charm)
    warn(world, helper, child, charm, problem)

    averted = False
    if magic_at_risk(charm, problem):
        if delay < 0:
            raise StoryError("delay cannot be negative")
    world.para()
    defy(world, child, charm)
    use_magic(world, child, charm, problem)
    alarm(world, helper, child, problem)

    severity = fire_severity(problem, delay)
    contained = is_resolved(remedy, problem, delay)
    world.facts["severity"] = severity

    world.para()
    if contained:
        rescue(world, helper, remedy, world.get("problem"), world.get("charm"))
        lesson(world, helper, child, charm)
        world.para()
        magical_fix(world, helper, child, remedy, setting)
        happy = True
    else:
        no_fix(world, helper, problem)
        world.say("The whole thing got away from everybody, and they had to back off and let the dust settle.")
        happy = False

    world.para()
    ending_image(world, child, setting, happy)

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        charm=charm,
        problem=problem,
        remedy=remedy,
        happy=happy,
        contained=contained,
        averted=averted,
        delay=delay,
        charmed=True,
    )
    return world


SETTINGS = {
    "bayou": Setting("bayou", "bayou", "warm and breezy", "A heron stood so still it looked painted on the sky.", "the bayou"),
    "porch": Setting("porch", "porch", "golden and slow", "A rocking chair creaked like it knew every family secret.", "the porch"),
    "garden": Setting("garden", "garden", "bright and humming", "A sunflower leaned over so far it seemed to listen to the ants.", "the garden"),
}

CHARMS = {
    "lantern": MagicCharm("lantern", "a little magic lantern", "blue and gold", "it can wake up trouble if used wrong", "keep it gentle"),
    "jar": MagicCharm("jar", "a glass jar full of glow", "like a summer lightning bug", "it can muddle a spell", "hold it steady"),
    "bell": MagicCharm("bell", "a silver wishing bell", "clear as creek water", "it can ring up a fuss", "ring it soft"),
}

PROBLEMS = {
    "pump": Problem("pump", "the old water pump", "making the yard dry as toast", "making the whole yard grow mean and dusty", spread=2),
    "gator": Problem("gator", "the little swamp gate", "slamming itself open and shut", "clattering loose and scaring everything in sight", spread=3),
    "sun": Problem("sun", "the porch swing shade", "sliding away from the bench", "leaving the bench hot enough to fry an egg", spread=2),
}

REMEDIES = {
    "fan": Remedy("fan", 3, 4, "fanned {problem} until the bad spell blew apart", "fanned at {problem}, but the spell kept huffing", "a hand-cranked fan"),
    "song": Remedy("song", 2, 3, "sang a slow song and soothed {problem} right down", "sang at {problem}, but the spell stayed jumpy", "a slow, low song"),
    "salt": Remedy("salt", 3, 5, "sprinkled a small circle of salt and boxed the spell in", "sprinkled salt, but the trouble slipped through", "a small circle of salt"),
}

NAMES_GIRL = ["June", "Lila", "Maggie", "Ruby", "Nell", "Sadie", "Daisy", "Ella"]
NAMES_BOY = ["Bo", "Tom", "Luke", "Hank", "Jesse", "Will", "Beau", "Ollie"]
TRAITS = ["curious", "careful", "bright-eyed", "stubborn", "cheerful"]

CURATED = [
    StoryParams("porch", "lantern", "pump", "fan", "June", "girl", "Aunt May", "aunt", 0),
    StoryParams("bayou", "jar", "gator", "song", "Bo", "boy", "Uncle Ray", "uncle", 0),
    StoryParams("garden", "bell", "sun", "salt", "Maggie", "girl", "Aunt June", "aunt", 1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid in CHARMS:
            for pid in PROBLEMS:
                if magic_at_risk(CHARMS[cid], PROBLEMS[pid]):
                    combos.append((sid, cid, pid))
    return combos


@dataclass
class StoryParams:
    setting: str
    charm: str
    problem: str
    remedy: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story for a 3-to-5-year-old that includes the word "southern" and a little magic.',
        f"Tell a southern tall tale where {f['child'].id} finds {f['charm'].label} and has to fix {f['problem'].label} with help from {f['helper'].id}.",
        f'Write a gentle magic story with a porch-or-bayou feeling, a big funny image, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, charm, problem, remedy = f["child"], f["helper"], f["charm"], f["problem"], f["remedy"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {helper.id}, with {charm.label} and {problem.label} causing the trouble.",
        ),
        QAItem(
            question="What went wrong in the story?",
            answer=f"{problem.label} started {problem.risk}, and the magic {charm.label} made the trouble grow too wild to ignore.",
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"{helper.id} used {remedy.qa_text} so the trouble settled down and the magic behaved again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does the word southern mean in a story?", "Southern means it has a feeling of the South, with warm weather, porch talk, and a homey pace."),
        QAItem("What is a tall tale?", "A tall tale is a story with big, funny exaggerations that still stays easy to follow."),
        QAItem("Why can magic be tricky?", "Magic can be tricky because if it is not handled carefully, it may make a small problem grow bigger."),
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
    return "\n".join(lines)


def explain_rejection(charm: MagicCharm, problem: Problem) -> str:
    return f"(No story: {charm.label} can make magic, but {problem.label} does not give the right kind of trouble.)"


def explain_remedy(rid: str) -> str:
    r = REMEDIES[rid]
    return f"(Refusing remedy '{rid}': it scores too low on common sense (sense={r.sense} < 2).)"


ASP_RULES = r"""
magic_problem(C, P) :- makes_magic(C), cursed(P).
sensible(R) :- remedy(R), sense(R, S), S >= sense_min(M), sense_min(M).
resolved(R, P, D) :- remedy(R), power(R, Pow), severity(P, Sev), Pow >= Sev.
outcome(happy) :- chosen_remedy(R), chosen_problem(P), chosen_delay(D), resolved(R, P, D).
outcome_sad :- chosen_remedy(R), chosen_problem(P), chosen_delay(D), not resolved(R, P, D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.makes_magic:
            lines.append(asp.fact("makes_magic", cid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, p.spread))
        lines.append(asp.fact("cursed", pid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show magic_problem/2."))
    return sorted(set(asp.atoms(model, "magic_problem")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1.\n#show outcome_sad/0."))
    outs = asp.atoms(model, "outcome")
    if outs:
        return outs[0][0]
    if asp.atoms(model, "outcome_sad"):
        return "sad"
    return "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP vs Python valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, charm=None, problem=None, remedy=None, child=None, child_gender=None, helper=None, helper_gender=None, delay=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke-generated a story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    for p in CURATED:
        if asp_outcome(p) not in {"happy", "sad"}:
            rc = 1
    print("OK: verification completed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Southern magic tall tale story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["aunt", "uncle", "mother", "father"])
    ap.add_argument("--delay", type=int, default=None)
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
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        raise StoryError(explain_remedy(args.remedy))
    combos = valid_combos()
    if args.charm and args.problem:
        if (args.charm, args.problem) not in [(c, p) for _, c, p in combos]:
            raise StoryError(explain_rejection(CHARMS[args.charm], PROBLEMS[args.problem]))
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.charm is None or c[1] == args.charm) and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, problem = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(k for k, r in REMEDIES.items() if r.sense >= 2))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or rng.choice(["aunt", "uncle", "mother", "father"])
    helper_pool = {
        "aunt": ["Aunt May", "Aunt June", "Aunt Belle"],
        "uncle": ["Uncle Ray", "Uncle Eli", "Uncle Bo"],
        "mother": ["Momma Rose", "Mama Lou", "Mother Clara"],
        "father": ["Papa Joe", "Daddy Sam", "Father Ben"],
    }[helper_gender]
    helper = args.helper or rng.choice(helper_pool)
    delay = 0 if args.delay is None else args.delay
    return StoryParams(setting, charm, problem, remedy, child, child_gender, helper, helper_gender, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHARMS[params.charm], PROBLEMS[params.problem], REMEDIES[params.remedy], params.child, params.child_gender, params.helper, params.helper_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in world_knowledge_qa(world)]],
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


def _make_default_params(rng: random.Random) -> StoryParams:
    return resolve_params(argparse.Namespace(setting=None, charm=None, problem=None, remedy=None, child=None, child_gender=None, helper=None, helper_gender=None, delay=None), rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show magic_problem/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible charm/problem pairs:")
        for c, p in asp_valid_combos():
            print(c, p)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
