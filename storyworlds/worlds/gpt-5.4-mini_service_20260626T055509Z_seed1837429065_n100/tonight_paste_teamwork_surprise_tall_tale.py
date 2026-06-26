#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/tonight_paste_teamwork_surprise_tall_tale.py
==============================================================================================================

A compact, standalone story world in a tall-tale style.

Premise seed:
- tonight
- paste
- teamwork
- surprise

Core tale:
A tiny riverside town needs a loose poster, map, or kite-fixed-to-a-barn sort of problem solved tonight.
The hero and a helper discover a surprising use for paste: it becomes the last-needed ingredient in a teamwork repair.
The story turns on a forecasted failure, then resolves with a cooperative fix and a surprising finish image.

This script is intentionally self-contained and stdlib-only unless ASP modes are used.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Job:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


def _r_splatter(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("pastey", "dusty"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.entities.values():
                if item.kind == "thing" and item.worn_by == actor.id and item.region in world.zone:
                    sig = ("splatter", actor.id, item.id, mess)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters[mess] = item.meters.get(mess, 0.0) + 1
                    item.meters["ruined"] = item.meters.get("ruined", 0.0) + 1
                    out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} in a blink.")
    return out


def _r_help_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.kind != "thing" or item.meters.get("ruined", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("help", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.get(item.caretaker)
        helper.memes["duty"] = helper.memes.get("duty", 0.0) + 1
        out.append(f"That would mean more work for {helper.label}.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_done"):
        return out
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    fix = world.facts.get("fix")
    prize = world.facts.get("prize")
    job = world.facts.get("job")
    if not (hero and helper and fix and prize and job):
        return out
    if hero.memes.get("teamwork", 0.0) < THRESHOLD:
        return out
    sig = ("surprise", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["surprise_done"] = True
    out.append(f"And then came the surprise: {helper.label} had saved the best bit for last.")
    return out


CAUSAL_RULES = [_r_splatter, _r_help_work, _r_surprise]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_damage(world: World, actor: Entity, job: Job, prize_id: str) -> dict:
    sim = world.copy()
    do_job(sim, sim.get(actor.id), job, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "ruined": prize.meters.get("ruined", 0.0) >= THRESHOLD,
        "work": sum(e.memes.get("duty", 0.0) for e in sim.characters()),
    }


def do_job(world: World, actor: Entity, job: Job, narrate: bool = True) -> None:
    if job.id not in world.setting.affords:
        return
    world.zone = {"hands", "torso"}
    actor.meters[job.mess] = actor.meters.get(job.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, job: Job, prize_cfg: Prize, fix_def: Fix,
         hero_name: str, helper_name: str, hero_type: str = "boy",
         helper_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["small", "spry"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["bright", "brave"]))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["love"] = 1
    helper.memes["care"] = 1

    world.say(
        f"Tonight, in the little river town, {hero.id} was a small {hero.type} with big hopes and a bigger hat."
    )
    world.say(
        f"{hero.id} loved to {job.verb}, and the whole town said the {job.keyword} tricks were taller than the church bell."
    )
    world.say(
        f"Before the stars climbed high, {helper.id} had brought {hero.id} {hero.pronoun('object')} {prize.phrase}."
    )
    world.say(
        f"{hero.id} loved {prize.label} and wore {prize.it()} as if the moon itself had stitched it."
    )

    world.para()
    world.say(
        f"At the old workbench, {hero.id} and {helper.id} found a surprise: the {job.keyword} paste had gone runny."
    )
    world.say(
        f"{hero.id} wanted to {job.verb} right away, but {helper.id} lifted a finger and looked at the {prize.label}."
    )

    pred = predict_damage(world, hero, job, prize.id)
    if pred["ruined"]:
        world.say(
            f'"If you rush now, your {prize.label} will be {job.soil}," {helper.id} said. "And I would have to clean it."'
        )

    hero.memes["teamwork"] = 1
    hero.memes["surprise"] = 0
    world.say(
        f"{hero.id} stopped, nodded, and helped stir the paste with {helper.id} instead of bolting off like a windblown kite."
    )
    world.say(
        f'They mixed, measured, and laughed until the paste was smooth enough to hold a penny and light enough to float a feather.'
    )

    world.para()
    world.say(
        f"Then {helper.id} showed the surprise bit: {fix.label} was not for a machine at all, but for the town banner that had split in the breeze."
    )
    world.say(
        f"Together they used {fix.label} to mend it, and the banner stood up straighter than a circus tent in a thunderstorm."
    )
    world.say(
        f"By the time they were done, {hero.id} could {job.gerund}, {prize.label} stayed clean, and the whole town cheered the teamwork."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        job=job,
        fix=fix_def,
        setting=setting,
        predicted=pred,
    )
    return world


SETTINGS = {
    "riverside": Setting(place="the riverside town", outdoor=True, affords={"paste"}),
    "workshop": Setting(place="the lantern workshop", outdoor=True, affords={"paste"}),
    "fairground": Setting(place="the fairground lot", outdoor=True, affords={"paste"}),
}

JOBS = {
    "paste": Job(
        id="paste",
        verb="paste the poster on the tall town board",
        gerund="pasting posters on the tall board",
        rush="dash to the board with a handful of paste",
        mess="pastey",
        soil="sticky and spotted",
        keyword="paste",
        surprise="poster",
        tags={"paste", "teamwork", "surprise"},
    )
}

PRIZES = {
    "coat": Prize(label="coat", phrase="a bright parade coat", type="coat", region="torso"),
    "apron": Prize(label="apron", phrase="a clean cooking apron", type="apron", region="torso"),
    "banner": Prize(label="banner", phrase="a striped banner", type="banner", region="torso"),
}

FIXES = [
    Fix(
        id="mender",
        label="the long glue brush",
        prep="use the long glue brush",
        tail="held the banner like a proud sail",
        guards={"pastey"},
        covers={"hands", "torso"},
    ),
]

NAMES = ["Milo", "June", "Penny", "Otis", "Nell", "Iris", "Arlo", "Ruby"]
HELPERS = ["Sally", "Bess", "Hattie", "Joan", "Mabel", "Wren", "Luna"]
TRAITS = ["nimble", "cheerful", "bold", "curious", "lively"]


@dataclass
class StoryParams:
    place: str
    job: str
    prize: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world with teamwork and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    job = args.job or "paste"
    prize = args.prize or rng.choice(list(PRIZES))
    hero_name = args.hero_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPERS if n != hero_name])
    return StoryParams(place=place, job=job, prize=prize, hero_name=hero_name, helper_name=helper_name)


def _story_intro(world: World) -> str:
    hero = world.facts["hero"]
    return f"{hero.id} was the kind of child who could hear a whisper in a windstorm."


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, job, prize = f["hero"], f["helper"], f["job"], f["prize"]
    return [
        'Write a short tall tale for a young child that includes the word "tonight" and the word "paste".',
        f"Tell a story where {hero.id} and {helper.id} solve a problem together with paste and end with a surprise.",
        f"Write a gentle tall tale about teamwork in {f['setting'].place} where a {prize.label} stays clean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, job, prize = f["hero"], f["helper"], f["job"], f["prize"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who worked with {helper.id} in {f['setting'].place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the paste?",
            answer=f"{hero.id} wanted to {job.verb}, but first {hero.id} had to work with {helper.id}.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id} to slow down?",
            answer=f"{helper.id} knew the {prize.label} would get {job.soil} if {hero.id} rushed in too fast.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The surprise was that the paste helped fix the town banner, and the teamwork made the whole town cheer.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, the work was finished together, the {prize.label} stayed clean, and {hero.id} felt proud of the teamwork.",
        ),
    ]


KNOWLEDGE = {
    "paste": (
        "What is paste?",
        "Paste is a sticky substance used to hold paper or light materials together.",
    ),
    "teamwork": (
        "What is teamwork?",
        "Teamwork means people help each other and work together to do a job.",
    ),
    "surprise": (
        "What is a surprise?",
        "A surprise is something unexpected that happens or gets revealed.",
    ),
    "banner": (
        "What is a banner?",
        "A banner is a long piece of cloth or paper with words or pictures on it.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["paste", "teamwork", "surprise", "banner"]:
        q, a = KNOWLEDGE[tag]
        out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_job(J) :- job(J).
valid_prize(R) :- prize(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for j in JOBS:
        lines.append(asp.fact("job", j))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_place/1."))
    if asp.atoms(model, "valid_place"):
        print("OK: ASP loaded.")
        return 0
    print("ASP check failed.")
    return 1


def _valid_combo(place: str, job: str, prize: str) -> bool:
    return job in SETTINGS[place].affords and prize in PRIZES and job in JOBS


CURATED = [
    StoryParams(place="riverside", job="paste", prize="banner", hero_name="Milo", helper_name="Sally"),
    StoryParams(place="workshop", job="paste", prize="coat", hero_name="June", helper_name="Wren"),
    StoryParams(place="fairground", job="paste", prize="apron", hero_name="Arlo", helper_name="Bess"),
]


def resolve_invalid(args: argparse.Namespace) -> None:
    if args.job and args.job not in JOBS:
        raise StoryError("That job is not part of this little world.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("That prize is not part of this little world.")
    if args.place and args.job and not _valid_combo(args.place, args.job, args.prize or "banner"):
        raise StoryError("No honest story fits those exact choices.")


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        JOBS[params.job],
        PRIZES[params.prize],
        FIXES[0],
        params.hero_name,
        params.helper_name,
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
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

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
