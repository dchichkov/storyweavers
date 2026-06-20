#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/knee_problem_solving_sharing_magic_tall_tale.py
================================================================================

A standalone storyworld for a tall-tale-ish tiny domain about a child, a giant
knee, a shared problem, and a little bit of magic.

The premise is simple:
- Someone's big, grumbly knee makes a task hard.
- The characters try to solve it together.
- They share tools, courage, and a magical helper.
- The ending proves the problem changed in the world, not just in the prose.

This script follows the Storyweavers contract:
- stdlib only
- imports shared results eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python and ASP reasonableness gates
- produces state-driven stories and grounded QA
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
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "giant"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "giant": "giant"}.get(self.type, self.type)


@dataclass
class Problem:
    id: str
    label: str
    state: str
    size: str
    difficulty: int
    dangerous: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicAid:
    id: str
    label: str
    phrase: str
    power: int
    shares: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    helps: int
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


def _r_pain(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("strain", 0.0) < THRESHOLD:
            continue
        sig = ("pain", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["grit"] = e.memes.get("grit", 0.0) + 1
        out.append("__pain__")
    return out


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    if not helper:
        return out
    if helper.meters.get("shared_help", 0.0) < THRESHOLD:
        return out
    sig = ("shared", "help")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["hope"] = e.memes.get("hope", 0.0) + 1
    out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("pain", "physical", _r_pain), Rule("shared", "social", _r_shared)]


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


def problem_at_risk(problem: Problem) -> bool:
    return problem.dangerous or problem.difficulty >= 2


def reasonable_aid(aid: MagicAid, problem: Problem) -> bool:
    return aid.power >= problem.difficulty and aid.shares


def sensible_aids() -> list[MagicAid]:
    return [a for a in AIDS.values() if a.power >= 2 and a.shares]


def outcome_of(problem: Problem, aid: MagicAid) -> str:
    if not problem_at_risk(problem):
        return "no_problem"
    return "solved" if reasonable_aid(aid, problem) else "stuck"


def tall_tale_beat(name: str, problem: Problem) -> str:
    return f"{name} had a knee so big and grumbly it could stop a wagon and make a mule blink twice."


def predict_help(world: World, aid: MagicAid, problem: Problem) -> dict:
    sim = world.copy()
    sim.get("problem").meters["strain"] += problem.difficulty
    sim.get("helper").meters["shared_help"] += aid.power
    propagate(sim, narrate=False)
    solved = sim.get("problem").meters.get("strain", 0.0) < 1.0
    return {"solved": solved, "hope": sum(e.memes.get("hope", 0.0) for e in sim.entities.values())}


def solve_problem(world: World, hero: Entity, helper: Entity, problem: Problem, aid: MagicAid, share: ShareItem) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    world.say(f"{hero.id} looked up at {helper.id} and the giant old knee. It was as knotty as a rope in a storm.")
    world.say(f'"We can fix it," {hero.id} said, and {helper.id} shared {share.phrase} from a pocket as deep as a rain barrel.')
    world.say(f"Then {helper.id} opened {aid.phrase}, and the magic sparkled like lightning caught in a jar.")
    helper.meters["shared_help"] = helper.meters.get("shared_help", 0.0) + aid.power
    problem_meter = world.get("problem")
    problem_meter.meters["strain"] = max(0.0, problem_meter.meters.get("strain", 0.0) - aid.power)
    propagate(world, narrate=False)
    world.say(f"The grumble in the knee eased. The big leg straightened like a gate swinging open after a long wind.")
    world.say(f"{hero.id} and {helper.id} laughed because the hard thing had become a doable thing together.")


def struggle(world: World, hero: Entity, helper: Entity, problem: Problem, aid: MagicAid) -> None:
    world.say(f"{hero.id} and {helper.id} tried their best, but the knee stayed stuck and stiff as a fence post.")
    world.say(f"Even the shiny {aid.label} was not enough by itself, and the problem would not budge.")
    world.say("So they had to think again, share what they had, and ask the magic to do more than sparkle.")


THEMES = {
    "hill": "the hill town",
    "harbor": "the harbor road",
    "prairie": "the windy prairie",
}

PROBLEMS = {
    "stuck_knee": Problem("stuck_knee", "a stuck knee", "stuck", "large", 2, dangerous=False, tags={"knee"}),
    "sore_knee": Problem("sore_knee", "a sore knee", "sore", "giant-sized", 3, dangerous=True, tags={"knee"}),
    "locked_knee": Problem("locked_knee", "a locked knee", "locked", "towering", 4, dangerous=True, tags={"knee"}),
}

AIDS = {
    "spark": MagicAid("spark", "spark bottle", "a spark bottle", 2, True, tags={"magic", "sharing"}),
    "glow": MagicAid("glow", "glow ribbon", "a glow ribbon", 3, True, tags={"magic", "sharing"}),
    "song": MagicAid("song", "singing charm", "a singing charm", 4, True, tags={"magic", "sharing"}),
}

SHARES = {
    "water": ShareItem("water", "water cup", "a cup of cool water", 1, tags={"sharing"}),
    "cloth": ShareItem("cloth", "soft cloth", "a soft cloth", 1, tags={"sharing"}),
    "stool": ShareItem("stool", "sturdy stool", "a sturdy stool", 1, tags={"sharing"}),
}

GIRL_NAMES = ["Mina", "Lily", "Ada", "Nora", "June"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Owen", "Max"]


@dataclass
class StoryParams:
    theme: str
    problem: str
    aid: str
    share: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for pid, p in PROBLEMS.items():
            if not problem_at_risk(p):
                continue
            for aid in AIDS.values():
                if not reasonable_aid(aid, p):
                    continue
                for sid in SHARES:
                    combos.append((theme, pid, aid.id, sid))
    return [(t, p, a) for t, p, a, s in combos]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about knee trouble, shared magic, and problem solving.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "giant"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.dangerous:
            lines.append(asp.fact("dangerous", pid))
        lines.append(asp.fact("difficulty", pid, p.difficulty))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("power", aid, a.power))
        if a.shares:
            lines.append(asp.fact("shares", aid))
    for sid in SHARES:
        lines.append(asp.fact("share", sid))
    lines.append(asp.fact("share_min", 1))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, P, A) :- theme(T), problem(P), aid(A), dangerous(P), power(A, Pow), difficulty(P, Dif), Pow >= Dif.
sensible(A) :- aid(A), shares(A), power(A, Pow), Pow >= 2.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) == {a.id for a in sensible_aids()}:
        print("OK: sensible aids match.")
    else:
        rc = 1
        print("MISMATCH in sensible aids.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.aid and not reasonable_aid(AIDS[args.aid], PROBLEMS[args.problem]):
        raise StoryError("That magic aid is not strong enough for that knee problem.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.problem is None or c[1] == args.problem)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, pid, aid = rng.choice(sorted(combos))
    sid = args.share or rng.choice(sorted(SHARES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or "giant"
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or "Old Harlan"
    return StoryParams(theme, pid, aid, sid, hero, hero_gender, helper, helper_gender)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(params.hero, "character", params.hero_gender, role="hero"))
    helper = world.add(Entity(params.helper, "character", params.helper_gender, role="helper"))
    problem = world.add(Entity("problem", "thing", "knee", role="problem"))
    problem.meters["strain"] = float(PROBLEMS[params.problem].difficulty)
    world.add(Entity("aid", "thing", AIDS[params.aid].label, role="aid"))
    world.add(Entity("share", "thing", SHARES[params.share].label, role="share"))

    world.say(f"On a day as wide as a prairie, {hero.id} met {helper.id} in {THEMES[params.theme]}.")
    world.say(tall_tale_beat(helper.id, PROBLEMS[params.problem]))
    world.para()
    world.say(f"{hero.id} did not sigh and quit. {hero.pronoun().capitalize()} brought a plan, a kind word, and a brave little grin.")
    world.say(f"{helper.id} shared {SHARES[params.share].phrase}, because even a giant knows that two hands are better than one.")
    world.para()
    if outcome_of(PROBLEMS[params.problem], AIDS[params.aid]) == "solved":
        solve_problem(world, hero, helper, PROBLEMS[params.problem], AIDS[params.aid], SHARES[params.share])
        outcome = "solved"
    else:
        struggle(world, hero, helper, PROBLEMS[params.problem], AIDS[params.aid])
        outcome = "stuck"
    world.facts.update(hero=hero, helper=helper, problem=problem, problem_cfg=PROBLEMS[params.problem],
                       aid=AIDS[params.aid], share=SHARES[params.share], outcome=outcome, theme=params.theme)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["problem_cfg"]
    return [
        f'Write a tall tale for a child that includes the word "knee" and shows a problem getting solved with shared magic.',
        f"Tell a funny big-hearted story about {f['hero'].id}, a giant, and {p.label} that gets better when they share a magical tool.",
        f"Write a short tall tale where the knee trouble looks impossible at first, but sharing and magic make the fix possible.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, p = f["hero"], f["helper"], f["problem_cfg"]
    return [
        QAItem("Who was the story about?", f"It was about {hero.id} and {helper.id}, who worked together on {p.label}."),
        QAItem("What was wrong?", f"{p.label.capitalize()} made the knee stiff and hard to use. The problem was big enough that they had to solve it together."),
        QAItem("How did they fix it?", f"They shared {f['share'].phrase} and used {f['aid'].phrase} to help the knee loosen. The magic worked because they did not keep the help to themselves."),
        QAItem("How did the ending change the world?", f"The knee became easier to move, so the hard problem turned into a solved one. The last image is of the big leg straightening and everyone laughing."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a knee?", "A knee is the joint in a leg that bends so people can walk, kneel, and stand up again."),
        QAItem("What does sharing mean?", "Sharing means letting someone else use or enjoy something with you. It can make a hard job easier."),
        QAItem("What is magic in a story?", "Magic is a special make-believe force that can do wonderful things in stories that would not happen in real life."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role} type={e.type}")
    lines.append(f"fired={sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("hill", "stuck_knee", "spark", "water", "Mina", "girl", "Old Harlan", "giant"),
    StoryParams("harbor", "sore_knee", "glow", "cloth", "Theo", "boy", "Big Marla", "giant"),
    StoryParams("prairie", "locked_knee", "song", "stool", "Nora", "girl", "Uncle Bram", "giant"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible aids: {', '.join(asp_sensible())}")
        for t, p, a in asp_valid_combos():
            print(t, p, a)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
