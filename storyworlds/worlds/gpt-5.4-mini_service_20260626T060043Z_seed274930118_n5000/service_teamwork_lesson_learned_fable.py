#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/service_teamwork_lesson_learned_fable.py
===============================================================================================

A small fable-like storyworld about service work, teamwork, and a lesson learned.

Premise seed:
- A little animal tries to do an important service job alone.
- The job goes wrong or becomes too hard.
- Friends help, each with a useful skill.
- The animal learns that asking for help makes the work safer, quicker, and kinder.

This world is intentionally tiny and classical:
- typed entities with meters and memes
- a forward-simulated world model
- a reasonableness gate with a matching ASP twin
- child-facing prose, ending in a clear moral-like lesson
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    tool: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "mess": 0.0, "progress": 0.0, "burden": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "frustration": 0.0, "trust": 0.0, "joy": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sheep", "goat", "mouse", "owl", "rabbit", "fox", "squirrel", "hedgehog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Job:
    id: str
    verb: str
    gerund: str
    mess: str
    risk: str
    difficult: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.job: Optional[Job] = None
        self.tools_used: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.job = self.job
        clone.tools_used = list(self.tools_used)
        clone.paragraphs = [[]]
        return clone


def has_helper(world: World) -> bool:
    return sum(1 for e in world.characters() if e.id != world.facts["hero"].id) >= 1


def need_teamwork(job: Job) -> bool:
    return bool(job.requires)


def reasonableness_gate(setting: Setting, job: Job, tool: Optional[Tool]) -> bool:
    return job.id in setting.affords and (tool is not None or not job.requires)


def predict_outcome(world: World, hero: Entity, job: Job, tool: Optional[Tool]) -> dict:
    sim = world.copy()
    _start_job(sim, sim.get(hero.id), job, narrate=False)
    if tool:
        _use_tool(sim, sim.get(hero.id), tool, narrate=False)
    _ask_for_help(sim, sim.get(hero.id), narrate=False)
    return {
        "mess": sim.facts.get("messy", False),
        "progress": sim.get(hero.id).meters["progress"],
        "trust": sim.get(hero.id).memes["trust"],
    }


def _start_job(world: World, actor: Entity, job: Job, narrate: bool = True) -> None:
    if job.id not in world.setting.affords:
        return
    actor.memes["pride"] += 1
    actor.meters["progress"] += 1
    actor.meters["mess"] += 1
    world.facts["started"] = True
    world.facts["messy"] = True
    if narrate:
        world.say(f"{actor.id} began to {job.verb} all by {actor.pronoun('object')}.")


def _use_tool(world: World, actor: Entity, tool: Tool, narrate: bool = True) -> None:
    actor.meters["progress"] += 1
    actor.memes["trust"] += 1
    world.facts.setdefault("tools", []).append(tool.id)
    world.tools_used.append(tool.id)
    if narrate:
        world.say(f"{actor.id} used {tool.label}, and the work became a little easier.")


def _ask_for_help(world: World, actor: Entity, narrate: bool = True) -> list[str]:
    out: list[str] = []
    helpers = [e for e in world.characters() if e.id != actor.id]
    if not helpers:
        return out
    for h in helpers:
        sig = ("help", h.id, actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        h.memes["joy"] += 1
        actor.memes["trust"] += 1
        actor.meters["progress"] += 1
        out.append(f"{h.id} came over to help.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, job: Job, tool: Optional[Tool], hero_name: str, helper_name: str) -> World:
    world = World(setting)
    world.job = job
    hero = world.add(Entity(id=hero_name, kind="character", type="hedgehog"))
    helper = world.add(Entity(id=helper_name, kind="character", type="rabbit"))
    object_name = {
        "cart": "old cart",
        "lantern": "lantern",
        "wheel": "water wheel",
        "gate": "garden gate",
    }.get(job.id, job.id)
    thing = world.add(Entity(
        id="thing",
        type=job.id,
        label=object_name,
        phrase=f"the {object_name}",
        caretaker=hero.id,
    ))

    world.say(f"{hero.id} lived near {setting.place} and wanted to keep things neat and useful.")
    world.say(f"{hero.id} knew how to {job.verb}, and loved the feeling of a job well done.")
    world.say(f"One day, {hero.id} saw {thing.phrase} and decided to {job.verb} {thing.phrase} before dusk.")

    world.para()
    _start_job(world, hero, job)
    world.say(f"But {job.risk} made the work harder than {hero.id} expected.")
    hero.memes["frustration"] += 1
    if tool:
        _use_tool(world, hero, tool)
    else:
        world.say(f"{hero.id} tried to keep going, but the task felt heavy and slow.")

    world.say(f"{hero.id} looked at the unfinished work and finally called for a friend.")
    _ask_for_help(world, hero)

    world.para()
    helper.memes["joy"] += 1
    helper.memes["trust"] += 1
    hero.memes["lesson"] += 1
    hero.memes["trust"] += 1
    hero.memes["joy"] += 1
    hero.memes["frustration"] = max(0.0, hero.memes["frustration"] - 1)

    if job.id == "cart":
        world.say(f"{helper.id} held the wheel steady while {hero.id} tightened the loose side.")
        world.say(f"Together they pushed the cart onto the path, and it rolled straight and smooth.")
    elif job.id == "lantern":
        world.say(f"{helper.id} wiped the glass while {hero.id} trimmed the wick.")
        world.say(f"Soon the lantern shone bright, like a small star at the end of the road.")
    elif job.id == "wheel":
        world.say(f"{helper.id} splashed water onto the dry blades while {hero.id} cleared the stuck leaves.")
        world.say(f"Then the wheel turned again, and the stream hummed a happy tune.")
    else:
        world.say(f"{helper.id} braced the gate while {hero.id} fixed the latch.")
        world.say(f"At last the gate swung shut with a neat little click.")

    world.say(f"{hero.id} smiled and said, \"A job is easier when friends lend their paws.\"")
    world.say(f"And {hero.id} learned that service can be a kind of teamwork, not a lonely test.")

    world.facts.update(
        hero=hero,
        helper=helper,
        thing=thing,
        job=job,
        tool=tool,
        lesson=True,
        teamwork=True,
    )
    return world


SETTINGS = {
    "barnyard": Setting(place="the barnyard", affords={"cart", "gate"}),
    "riverside": Setting(place="the riverside", affords={"wheel", "cart"}),
    "village": Setting(place="the village path", affords={"lantern", "gate"}),
    "orchard": Setting(place="the orchard", affords={"gate", "cart"}),
}

JOBS = {
    "cart": Job(
        id="cart",
        verb="service the cart",
        gerund="servicing the cart",
        mess="dust",
        risk="one wheel was loose",
        difficult="the cart was too heavy to move alone",
        keyword="cart",
        tags={"work", "wood"},
        requires={"helper"},
    ),
    "lantern": Job(
        id="lantern",
        verb="service the lantern",
        gerund="servicing the lantern",
        mess="soot",
        risk="the glass was grimy and the wick was short",
        difficult="the lantern needed careful hands",
        keyword="service",
        tags={"light", "glow"},
        requires={"helper"},
    ),
    "wheel": Job(
        id="wheel",
        verb="service the wheel",
        gerund="servicing the wheel",
        mess="mud",
        risk="the wheel was stuck with leaves and grit",
        difficult="the wheel turned slowly",
        keyword="service",
        tags={"water", "motion"},
        requires={"helper"},
    ),
    "gate": Job(
        id="gate",
        verb="service the gate",
        gerund="servicing the gate",
        mess="rust",
        risk="the latch was jammed",
        difficult="the gate needed steady hands",
        keyword="service",
        tags={"metal", "home"},
        requires={"helper"},
    ),
}

TOOLS = {
    "oiler": Tool(id="oiler", label="a small oil can", helps={"rust", "jammed"}, covers={"metal"}, prep="oil the hinge", tail="oiled the hinge"),
    "cloth": Tool(id="cloth", label="a soft cloth", helps={"soot", "dust"}, covers={"glass"}, prep="wipe the glass", tail="wiped the glass"),
    "brush": Tool(id="brush", label="a scrub brush", helps={"mud", "dust"}, covers={"wood"}, prep="scrub the wheel", tail="scrubbed the wheel"),
}

HEROES = ["Holly", "Milo", "Pip", "Nora", "Toby", "Mina"]
HELPERS = ["Rae", "Bram", "June", "Otis", "Wren", "Pia"]


@dataclass
class StoryParams:
    setting: str
    job: str
    tool: Optional[str]
    hero: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, Optional[str]]]:
    combos: list[tuple[str, str, Optional[str]]] = []
    for sid, setting in SETTINGS.items():
        for jid in setting.affords:
            job = JOBS[jid]
            if job.requires:
                for tid, tool in TOOLS.items():
                    if job.id == "cart" and tid == "brush":
                        continue
                    combos.append((sid, jid, tid))
            else:
                combos.append((sid, jid, None))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld about service, teamwork, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
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
    if args.job and args.setting and args.job not in SETTINGS[args.setting].affords:
        raise StoryError("That job does not fit the chosen setting.")
    if args.job and args.tool is None and JOBS[args.job].requires:
        pass
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.job is None or c[1] == args.job)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, job, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    return StoryParams(setting=setting, job=job, tool=tool, hero=hero, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable for a young child about {f['hero'].id} learning that service work goes better with teamwork.",
        f"Tell a gentle story where {f['hero'].id} tries to {f['job'].verb} and a friend helps with the job.",
        f"Write a simple moral tale that includes the word 'service' and ends with a lesson about asking for help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    job = f["job"]
    setting = world.setting
    tool = f["tool"]
    tool_text = tool.label if tool else "no special tool"
    return [
        QAItem(
            question=f"What job did {hero.id} try to do at {setting.place}?",
            answer=f"{hero.id} tried to {job.verb} at {setting.place}. The work was about keeping something useful and safe.",
        ),
        QAItem(
            question=f"Why did {hero.id} need help?",
            answer=f"{job.difficult.capitalize()}, and {job.risk}. {helper.id} helped so the work could be finished more safely and quickly.",
        ),
        QAItem(
            question=f"What tool, if any, did {hero.id} use during the work?",
            answer=f"{hero.id} used {tool_text}. It helped with the hard part of the job.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that service is easier when friends work together, and that asking for help is wise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or animals work together, each doing a part of the job, so the whole task gets done better.",
        ),
        QAItem(
            question="What does it mean to service something?",
            answer="To service something means to clean it, fix it, or care for it so it keeps working well.",
        ),
        QAItem(
            question="Why is a lesson learned in a fable important?",
            answer="A lesson learned is important because it helps the character and the reader remember a good way to act next time.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    if world.tools_used:
        lines.append(f"  tools used: {world.tools_used}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(barnyard; riverside; village; orchard).
affords(barnyard, cart). affords(barnyard, gate).
affords(riverside, wheel). affords(riverside, cart).
affords(village, lantern). affords(village, gate).
affords(orchard, gate). affords(orchard, cart).

job(cart; lantern; wheel; gate).

requires(cart, helper). requires(lantern, helper).
requires(wheel, helper). requires(gate, helper).

tool(oiler; cloth; brush).

valid(Setting, Job, Tool) :- affords(Setting, Job), requires(Job, helper), tool(Tool).
valid(Setting, Job, none) :- affords(Setting, Job), not requires(Job, helper).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for jid in SETTINGS[sid].affords:
            lines.append(asp.fact("affords", sid, jid))
    for jid, job in JOBS.items():
        lines.append(asp.fact("job", jid))
        if job.requires:
            lines.append(asp.fact("requires", jid, "helper"))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(a, b, c if c is not None else "none") for a, b, c in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        JOBS[params.job],
        TOOLS.get(params.tool) if params.tool else None,
        params.hero,
        params.helper,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, job, tool) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("barnyard", "cart", "oiler", "Holly", "Rae"),
            StoryParams("village", "lantern", "cloth", "Milo", "June"),
            StoryParams("riverside", "wheel", "brush", "Nora", "Otis"),
            StoryParams("orchard", "gate", "oiler", "Pip", "Wren"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero}: {p.job} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
