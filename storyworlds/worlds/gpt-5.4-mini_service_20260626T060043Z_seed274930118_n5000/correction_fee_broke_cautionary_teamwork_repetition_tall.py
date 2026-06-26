#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/correction_fee_broke_cautionary_teamwork_repetition_tall.py
====================================================================================================

A small, self-contained story world in a tall-tale style.

Premise:
- A river town keeps a very tall weather sign on a very tall pole.
- The sign is broken after a windy night.
- A correction fee must be paid to the sign-maker before the mistake can be fixed.
- A cautionary warning reminds everyone not to rush the job.
- Teamwork and repetition carry the day: everyone helps, and the fix is tested again and again.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- a world model that drives prose
- invalid explicit choices raise StoryError
- inline ASP twin plus Python reasonableness gate
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the river town square"


@dataclass
class Problem:
    id: str
    broken_thing: str
    broken_phrase: str
    correction_target: str
    fee_name: str
    caution: str
    repetition_phrase: str
    teamwork_helper: str
    fix_verb: str
    fixed_image: str


@dataclass
class StoryParams:
    setting: str
    problem: str
    seed: Optional[int] = None


SETTINGS = {
    "square": Setting(place="the river town square"),
}


PROBLEMS = {
    "sign": Problem(
        id="sign",
        broken_thing="sign",
        broken_phrase="the tall town sign",
        correction_target="the crooked letters",
        fee_name="correction fee",
        caution="Measure twice before you climb, and never trust a windy board on the first try.",
        repetition_phrase="again and again",
        teamwork_helper="the miller, the baker, and the lantern man",
        fix_verb="straighten",
        fixed_image="the tall town sign standing straight as a broom handle at dawn",
    )
}


HERO_NAMES = ["Mabel", "Eli", "June", "Otis", "Ruth", "Hank"]


class World:
    def __init__(self, setting: Setting, problem: Problem) -> None:
        self.setting = setting
        self.problem = problem
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _narrate(world: World, text: str) -> None:
    world.say(text)


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def reasonableness_gate(setting: Setting, problem: Problem) -> None:
    if not setting.place or not problem.broken_thing:
        raise StoryError("This world needs a setting and a broken thing.")
    if "fee" not in problem.fee_name:
        raise StoryError("The story needs a real correction fee to make the correction matter.")
    if "broken" not in problem.broken_phrase and problem.id != "sign":
        raise StoryError("The broken object must be plainly broken enough to drive the tale.")


def resolve_supporting_cast(rng: random.Random) -> list[str]:
    helpers = ["the miller", "the baker", "the lantern man"]
    rng.shuffle(helpers)
    return helpers


def tell(setting: Setting, problem: Problem, hero_name: str, rng: random.Random) -> World:
    world = World(setting, problem)

    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    mayor = world.add(Entity(id="mayor", kind="character", type="woman", label="the mayor"))
    fixer = world.add(Entity(id="fixer", kind="character", type="man", label="the sign-maker"))
    sign = world.add(Entity(
        id="sign",
        type="thing",
        label="town sign",
        phrase=problem.broken_phrase,
        owner=mayor.id,
        caretaker=fixer.id,
    ))

    helpers = resolve_supporting_cast(rng)
    world.facts.update(hero=hero, mayor=mayor, fixer=fixer, sign=sign, helpers=helpers)

    _narrate(world, f"In {setting.place}, there stood {problem.broken_phrase}, so tall it could tickle a cloud.")
    _narrate(world, f"Little {hero.id} loved that sign, because it told the whole town where to go and when to grin.")
    _narrate(world, f"Then a hard wind came by and left {problem.broken_phrase} broken and lopsided.")
    _narrate(world, f"The mayor said there was a {problem.fee_name} to pay before anyone could {problem.fix_verb} {problem.correction_target}.")

    world.para()
    _narrate(world, f"{problem.caution}")
    _add_meme(hero, "worry", 1)
    _add_meme(mayor, "care", 1)
    _add_meme(fixer, "duty", 1)
    _add_meter(sign, "broken", 1)

    _narrate(world, f"{hero.id} listened close and nodded, because a cautionary warning is worth two on a windy day.")
    _narrate(world, f"So {hero.id}, {helpers[0]}, {helpers[1]}, and {helpers[2]} got to work together.")

    world.para()
    _narrate(world, f"They climbed carefully, and then they climbed {problem.repetition_phrase}, because the first pull was not enough.")
    _narrate(world, f"The sign swayed. The rope sang. The ladder creaked like a fiddle in a thunderstorm.")
    _narrate(world, f"Still, nobody rushed. They measured, tied, and measured again.")
    _add_meter(sign, "steady", 1)
    _add_meme(hero, "hope", 1)
    _add_meme(hero, "joy", 1)

    world.para()
    _narrate(world, f"The mayor paid the {problem.fee_name}, the sign-maker made the {problem.correction_target} right, and everybody gave a cheer big enough to shake the sparrows loose.")
    _narrate(world, f"At last, the fix held.")
    _narrate(world, f"By sunset, {problem.fixed_image} shone over the square, and the whole town walked under it like it had never been broken at all.")

    world.facts["resolved"] = True
    world.facts["fee_paid"] = True
    world.facts["helpers_count"] = len(helpers)
    world.facts["repeated"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.problem
    return [
        f'Write a tall-tale story about {p.broken_phrase}, a {p.fee_name}, and a careful correction.',
        f"Tell a child-friendly story where a warning keeps a town from rushing a repair, and everyone works together.",
        f'Write a story that repeats a fix, a fee, and a brave little helper in a windy river town.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mayor: Entity = f["mayor"]
    sign: Entity = f["sign"]
    helpers = f["helpers"]
    p: Problem = world.problem
    return [
        QAItem(
            question=f"What broke in the river town square?",
            answer=f"{p.broken_phrase} broke, and it had to be corrected before the town could feel settled again.",
        ),
        QAItem(
            question=f"What did the mayor say had to be paid before the repair?",
            answer=f"The mayor said a {p.fee_name} had to be paid before the correction could happen.",
        ),
        QAItem(
            question=f"Who helped fix the broken sign?",
            answer=f"{hero.id}, {helpers[0]}, {helpers[1]}, and {helpers[2]} all helped, and the sign-maker guided the work.",
        ),
        QAItem(
            question=f"Why did nobody rush the repair?",
            answer=f"Because of the cautionary warning: {p.caution}",
        ),
        QAItem(
            question=f"What happened after they worked on the sign again and again?",
            answer=f"The correction held, and {p.fixed_image} was the ending image of the story.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fee?",
            answer="A fee is money paid for a service or a job, like paying someone to fix something carefully.",
        ),
        QAItem(
            question="What does correction mean?",
            answer="A correction is a change that fixes a mistake or makes something right again.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a warning to be careful and avoid trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
broken(X) :- thing(X), needs_fix(X).
needs_fix(sign).
fee_required(sign).
cautionary(sign).
teamwork(sign) :- helper(miller), helper(baker), helper(lantern_man).
repeat_fix(sign) :- teamwork(sign), fee_required(sign), cautionary(sign).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("thing", "sign"),
        asp.fact("needs_fix", "sign"),
        asp.fact("helper", "miller"),
        asp.fact("helper", "baker"),
        asp.fact("helper", "lantern_man"),
        asp.fact("fee_required", "sign"),
        asp.fact("cautionary", "sign"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show teamwork/1.\n#show repeat_fix/1.\n#show fee_required/1.\n"))
    teamwork = set(asp.atoms(model, "teamwork"))
    repeat_fix = set(asp.atoms(model, "repeat_fix"))
    fee_required = set(asp.atoms(model, "fee_required"))
    ok = teamwork == {("sign",)} and repeat_fix == {("sign",)} and fee_required == {("sign",)}
    if ok:
        print("OK: ASP twin agrees with the Python reasonableness gate.")
        return 0
    print("MISMATCH in ASP parity.")
    print("teamwork:", sorted(teamwork))
    print("repeat_fix:", sorted(repeat_fix))
    print("fee_required:", sorted(fee_required))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about correction, fee, broke, teamwork, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", choices=HERO_NAMES)
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
    setting = args.setting or "square"
    problem = args.problem or "sign"
    reasonableness_gate(SETTINGS[setting], PROBLEMS[problem])
    return StoryParams(
        setting=setting,
        problem=problem,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    rng = random.Random(params.seed or 0)
    hero_name = rng.choice(HERO_NAMES)
    world = tell(setting, problem, hero_name, rng)
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
    StoryParams(setting="square", problem="sign", seed=274930118),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show broken/1.\n#show teamwork/1.\n#show repeat_fix/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show broken/1.\n#show teamwork/1.\n#show repeat_fix/1.\n#show fee_required/1.\n"))
        print("broken:", sorted(set(asp.atoms(model, "broken"))))
        print("teamwork:", sorted(set(asp.atoms(model, "teamwork"))))
        print("repeat_fix:", sorted(set(asp.atoms(model, "repeat_fix"))))
        print("fee_required:", sorted(set(asp.atoms(model, "fee_required"))))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.problem} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
