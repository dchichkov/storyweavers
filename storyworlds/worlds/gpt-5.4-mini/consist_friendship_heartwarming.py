#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/consist_friendship_heartwarming.py
===================================================================

A small heartwarming story world about friendship, a shared circle of trust,
and a child learning that a good friend is not just someone who plays with you,
but someone who can be counted on when the day feels wobbly.

Seed story idea
---------------
A child feels left out because the play group has a rule: good friends consist
of kindness, listening, and keeping promises. When one friend forgets a turn or
loses their courage, the group helps, shares, and repairs hurt feelings. The
story ends with a warm image showing that the friendship is stronger than the
small problem.

This script is a standalone storyworld. It generates a complete story, three
Q&A sets, and optional ASP parity checks, following the repo's storyworld
contract.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Place:
    id: str
    label: str
    cozy: str
    shared_thing: str
    safe_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Friendship:
    id: str
    rule: str
    repair: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    kind: str
    label: str
    hurt: str
    fixable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class KindAct:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["hurt"] < THRESHOLD:
            continue
        sig = ("hurt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for friend in world.entities.values():
            if friend.role == "friend":
                friend.memes["concern"] += 1
        out.append("__hurt__")
    return out


def _r_together(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("together") and not world.facts.get("together_said"):
        world.facts["together_said"] = True
        for e in world.entities.values():
            if e.role in {"child", "friend"}:
                e.memes["joy"] += 1
        out.append("They felt better being together.")
    return out


CAUSAL_RULES = [Rule("hurt", "social", _r_hurt), Rule("together", "social", _r_together)]


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


def gentle_check(world: World, problem: Problem, act: KindAct) -> bool:
    return problem.fixable and act.sense >= 2 and act.power >= 1


def best_act() -> KindAct:
    return max(ACTS.values(), key=lambda a: a.sense)


def _do_problem(world: World, target: Entity) -> None:
    target.meters["hurt"] += 1
    propagate(world, narrate=False)


def predict_problem(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(target_id))
    return {"hurt": sim.get(target_id).meters["hurt"] >= THRESHOLD}


def introduce(world: World, child: Entity, friend: Entity, place: Place, friendship: Friendship) -> None:
    child.memes["hope"] += 1
    friend.memes["warmth"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {friend.id} met at {place.label}. "
        f"{place.cozy} {place.shared_thing} waited there, and the whole place felt calm."
    )
    world.say(
        f"They liked to say that friendship {friendship.rule}, because a real friend {friendship.comfort}."
    )


def need_help(world: World, child: Entity, place: Place, problem: Problem) -> None:
    world.say(
        f"But near {place.safe_spot}, something small went wrong: {problem.label}. "
        f"{child.id} looked down and felt {problem.hurt}."
    )


def promise(world: World, child: Entity, friend: Entity, friendship: Friendship) -> None:
    child.memes["wish"] += 1
    world.say(
        f'"{friendship.rule.capitalize()}," {friend.id} said softly, "and when one of us feels sad, the other stays close."'
    )
    world.say(
        f'{child.id} nodded. "That is what friends do," {child.pronoun()} said.'
    )


def tiny_worry(world: World, child: Entity, friend: Entity, problem: Problem) -> None:
    child.memes["worry"] += 1
    world.say(
        f'For a moment, {child.id} thought the day might turn gloomy because of {problem.label}.'
    )


def help_fix(world: World, helper: Entity, child: Entity, act: KindAct, problem: Problem) -> None:
    world.say(
        f'{helper.id} came over, {act.text.replace("{problem}", problem.label)}.'
    )
    world.say(
        f'Then {child.id} took a careful breath, and the small trouble began to feel lighter.'
    )


def fail_fix(world: World, helper: Entity, child: Entity, act: KindAct, problem: Problem) -> None:
    world.say(
        f'{helper.id} tried to help, but {act.fail.replace("{problem}", problem.label)}.'
    )
    world.say("The trouble stayed for a little while, and both friends had to try again together.")


def repair(world: World, child: Entity, friend: Entity, friendship: Friendship) -> None:
    child.memes["gratitude"] += 1
    friend.memes["warmth"] += 1
    world.facts["together"] = True
    world.say(
        f"{child.id} smiled at {friend.id}. {friendship.repair.capitalize()}, and the two of them made up."
    )
    propagate(world, narrate=False)


def ending(world: World, child: Entity, friend: Entity, place: Place, friendship: Friendship) -> None:
    child.memes["peace"] += 1
    friend.memes["peace"] += 1
    world.say(
        f"Before long, {child.id} and {friend.id} were sitting side by side at {place.safe_spot}, "
        f"sharing {place.shared_thing} again."
    )
    world.say(
        f"Their friendship was warm and steady, the kind that {friendship.rule} even after a small hurt."
    )


def tell(place: Place, friendship: Friendship, problem: Problem, act: KindAct,
         child_name: str = "Mia", child_type: str = "girl",
         friend_name: str = "Noah", friend_type: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child",
                             traits=["kind"], age=6))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend",
                              traits=["gentle"], age=6))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent",
                               label="the parent"))

    world.facts.update(place=place, friendship=friendship, problem=problem, act=act,
                       child=child, friend=friend, parent=parent)

    introduce(world, child, friend, place, friendship)
    world.para()
    need_help(world, child, place, problem)
    promise(world, child, friend, friendship)
    tiny_worry(world, child, friend, problem)

    world.para()
    pred = predict_problem(world, child.id)
    child.memes["care"] += 1
    if gentle_check(world, problem, act) and pred["hurt"]:
        help_fix(world, friend, child, act, problem)
        repair(world, child, friend, friendship)
        world.para()
        ending(world, child, friend, place, friendship)
        world.facts["outcome"] = "repaired"
    else:
        fail_fix(world, friend, child, act, problem)
        world.say(
            f"{parent.label_word.capitalize()} noticed, came over, and helped them turn the whole moment into a kinder one."
        )
        repair(world, child, friend, friendship)
        world.para()
        ending(world, child, friend, place, friendship)
        world.facts["outcome"] = "repaired"
    return world


PLACES = {
    "garden": Place("garden", "the garden", "Sunlight warmed the path, and", "a little wooden bench", "the reading corner", {"garden", "outdoor"}),
    "playroom": Place("playroom", "the playroom", "Soft rugs made the room feel safe, and", "a basket of blocks", "the window seat", {"indoor"}),
    "porch": Place("porch", "the porch", "The porch smelled like rain, and", "a potted plant", "the doorway step", {"porch"}),
}

FRIENDSHIPS = {
    "kindness": Friendship("kindness", "friendship consists of kindness, listening, and sharing", "they listened and tried again", "always stays gentle", {"kindness"}),
    "loyal": Friendship("loyal", "friendship consists of loyalty, patience, and helping", "they waited and helped", "stays close in a wobble", {"loyal"}),
    "steady": Friendship("steady", "friendship consists of trust, honesty, and care", "they told the truth and fixed it", "holds on when things feel tricky", {"steady"}),
}

PROBLEMS = {
    "spilled_crayons": Problem("spilled_crayons", "spilled crayons", "a box of crayons had tipped over", "a little worried"),
    "torn_picture": Problem("torn_picture", "torn picture", "one page had a tiny tear", "a little sad"),
    "lost_string": Problem("lost_string", "lost string", "the kite string had slipped away", "a little upset"),
}

ACTS = {
    "share_box": KindAct("share_box", 3, 2,
                         "picked up the crayons, sorted the colors, and set the red one back in the box",
                         "tried to sort the crayons, but the wind had already scattered them farther",
                         "picked up the crayons and sorted the colors", {"crayons"}),
    "mend_page": KindAct("mend_page", 3, 2,
                         "found tape, smoothed the page, and pressed the tear flat",
                         "looked for tape, but the page was folded so tightly that it would not mend yet",
                         "found tape and smoothed the page", {"paper"}),
    "find_string": KindAct("find_string", 2, 2,
                           "followed the path, found the string near the step, and handed it back",
                           "looked and looked, but the string had blown too far away",
                           "found the string and handed it back", {"string"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Leo", "Finn", "Max", "Owen", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for f in FRIENDSHIPS:
            for pr in PROBLEMS:
                if gentle_check(World(), PROBLEMS[pr], ACTS["share_box"] if pr == "spilled_crayons" else ACTS["mend_page"]):
                    combos.append((p, f, pr))
    return combos


@dataclass
class StoryParams:
    place: str
    friendship: str
    problem: str
    act: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "friendship": [("What is friendship?",
                    "Friendship is when people care about each other, share, listen, and help one another.")],
    "kindness": [("What does kindness mean?",
                  "Kindness means being gentle, helpful, and thoughtful with other people.")],
    "listening": [("Why is listening important?",
                   "Listening helps friends understand each other, so they can solve problems together.")],
    "sharing": [("Why do friends share?",
                 "Friends share so everyone feels included and cared for.")],
    "trust": [("What is trust?",
               "Trust is when you feel safe believing someone will try to do the right thing.")],
    "care": [("What does it mean to care about someone?",
              "It means you notice their feelings and want to help them feel better.")],
    "repair": [("Why is it good to fix mistakes?",
                "Fixing mistakes helps people feel better and keeps the friendship strong.")],
}
KNOWLEDGE_ORDER = ["friendship", "kindness", "listening", "sharing", "trust", "care", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child about friendship, using the word "consist" and a small problem that gets repaired.',
        f"Tell a gentle story where {f['child'].id} and {f['friend'].id} learn that friendship consist of {f['friendship'].rule.split(' consists of ')[1]}.",
        f"Write a soft, reassuring story where two friends help each other after {f['problem'].label}, and the ending feels warm.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, place, friendship, problem, act = f["child"], f["friend"], f["place"], f["friendship"], f["problem"], f["act"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, two friends who spent time together at {place.label}."),
        ("What small problem happened?",
         f"{problem.label.capitalize()} happened, and it made {child.id} feel a little sad at first."),
        ("How did they fix it?",
         f"They used kindness and then {act.qa_text}. That helped repair the moment and made the friendship feel safe again."),
        ("What did they learn about friendship?",
         f"They learned that friendship {friendship.rule}. In other words, good friends keep trying, listen carefully, and help each other feel better."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["friendship"].tags) | {"friendship", "kindness", "listening", "sharing", "trust", "care", "repair"}
    out: list[tuple[str, str]] = []
    for t in KNOWLEDGE_ORDER:
        if t in tags:
            out.extend(KNOWLEDGE[t])
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
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "kindness", "spilled_crayons", "share_box", "Mia", "girl", "Noah", "boy", "mother"),
    StoryParams("playroom", "steady", "torn_picture", "mend_page", "Lily", "girl", "Eli", "boy", "father"),
    StoryParams("porch", "loyal", "lost_string", "find_string", "Finn", "boy", "Zoe", "girl", "mother"),
]


def explain_rejection() -> str:
    return "(No story: the chosen pieces do not make a gentle, fixable friendship moment.)"


ASP_RULES = r"""
valid(P, F, Pr) :- place(P), friendship(F), problem(Pr), fixable(Pr).
outcome(repaired) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FRIENDSHIPS:
        lines.append(asp.fact("friendship", fid))
    for prid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
        if pr.fixable:
            lines.append(asp.fact("fixable", prid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming friendship story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--friendship", choices=FRIENDSHIPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.problem and args.act and not gentle_check(World(), PROBLEMS[args.problem], ACTS[args.act]):
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.friendship is None or c[1] == args.friendship)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, friendship, problem = rng.choice(sorted(combos))
    act = args.act or rng.choice(sorted(ACTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, friendship, problem, act, child, child_gender, friend, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], FRIENDSHIPS[params.friendship], PROBLEMS[params.problem], ACTS[params.act],
                 params.child, params.child_gender, params.friend, params.friend_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, friendship, problem) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.friend}: {p.friendship} / {p.problem}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
