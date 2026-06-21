#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fatal_install_curiosity_rhyming_story.py
=========================================================================

A small standalone storyworld for a rhyming, child-facing curiosity tale.

Premise
-------
A curious child wants to explore a new "install" project. The curiosity turns
risky when the child tries to help with a heavy, sharp, or dangerous part. A
careful grown-up stops the unsafe step, explains the "fatal" risk in gentle
language, and redirects the child to a safe helping task. The ending proves what
changed: the project gets finished, the child learns to ask first, and the room
feels calm again.

The world is designed to generate short rhyming stories with a clear beat:
setup, curious reach, warning/turn, and a safe ending.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
class Project:
    id: str
    place: str
    thing: str
    rhyme_a: str
    rhyme_b: str
    hazard: str
    install_task: str
    safe_task: str
    tool: str
    outcome_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    project: str
    response: str
    child: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    proj = world.get("project")
    if child.meters["risk"] >= THRESHOLD and proj.meters["hazard"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, proj in PROJECTS.items():
        for rid, resp in RESPONSES.items():
            if resp.sense >= SENSE_MIN and proj.hazard:
                combos.append((pid, rid))
    return combos


def would_be_fatal(proj: Project) -> bool:
    return "fatal" in proj.tags


def predict_risk(world: World, proj_id: str) -> dict:
    sim = world.copy()
    _attempt_install(sim, sim.get("child"), PROJECTS[proj_id], narrate=False)
    return {
        "risk": sim.get("child").meters["risk"],
        "hazard": sim.get("project").meters["hazard"],
    }


def _attempt_install(world: World, child: Entity, proj: Project, narrate: bool = True) -> None:
    child.meters["risk"] += 1
    world.get("project").meters["hazard"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, parent: Entity, proj: Project) -> None:
    world.say(
        f"Little {child.id} had a bright, bold, curious mind, and {child.pronoun()} "
        f"loved to help when things were on the grind. "
        f"{parent.id} was getting ready to {proj.install_task}, and the whole room "
        f"felt neat with a shiny new sign."
    )
    world.say(
        f"{child.id} peeked at the box and grinned at the sight; "
        f"the pieces looked clever, the screws looked light."
    )


def curiosity(world: World, child: Entity, proj: Project) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'But {child.id} was curious. "{proj.tool.capitalize()}? Ooh, what does it do?" '
        f"{child.pronoun().capitalize()} asked with delight."
    )
    world.say(
        f"{child.id} reached for the tricky part, just wanting to try; "
        f"the rhyming project looked simple, but that was a lie."
    )


def warn(world: World, parent: Entity, child: Entity, proj: Project) -> None:
    pred = predict_risk(world, proj.id)
    if pred["risk"] < THRESHOLD:
        return
    world.facts["fatal"] = would_be_fatal(proj)
    world.say(
        f'"Wait, sweetheart," {parent.id} said softly, "that step could be fatal '
        f"if we rush it, you see. Sharp edges and heavy parts need a grown-up's care; "
        f"let's keep those fingers safe and free."'
    )


def redirect(world: World, parent: Entity, child: Entity, proj: Project) -> None:
    child.memes["trust"] += 1
    world.say(
        f'{child.id} nodded and asked, "Then what can I do?" '
        f"{parent.id} smiled and pointed the way. "
        f'"You can hold the flashlight and hand me each screw; '
        f"you can help in a safe, small way."'
    )


def finish(world: World, parent: Entity, child: Entity, proj: Project, resp: Response) -> None:
    world.get("project").meters["hazard"] = 0.0
    body = resp.text.replace("{thing}", proj.thing)
    world.say(
        f"{parent.id} {body}."
    )
    world.say(
        f"The new {proj.thing} went up with a click and a gleam, and the room grew "
        f"calm like a soft little dream."
    )
    world.say(
        f"{child.id} helped with the safe parts, proud as could be; "
        f"now {child.pronoun()} knew curiosity is best when it asks first, you see."
    )
    world.say(proj.outcome_line)


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    proj = f["project_cfg"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id} getting a new {proj.thing} ready. "
         f"The child is curious, and the grown-up stays careful."),
        ("What did the child want to do?",
         f"{child.id} wanted to help install the {proj.thing}. {child.id} also wanted "
         f"to touch the tricky part, because curiosity made the piece look exciting."),
        ("Why did the parent warn the child?",
         f"{parent.id} warned {child.id} because that step could be fatal if they rushed it. "
         f"The sharp or heavy part needed a grown-up, so the child had to step back."),
    ]
    if f.get("resolved"):
        qa.append((
            "How was the problem solved?",
            f"{parent.id} gave {child.id} a safe job, and {child.id} helped with the "
            f"easy pieces instead. That let the project get finished without any danger."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the {proj.thing} installed, the room calm, and {child.id} "
            f"smiling at a safe, finished project. Curiosity stayed, but it learned to ask first."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["project_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    proj = f["project_cfg"]
    return [
        f'Write a rhyming story for a small child that includes the words "{proj.thing}" and "fatal".',
        f"Tell a curious story where {f['child'].id} wants to help install a {proj.thing}, but {f['parent'].id} keeps the danger safe.",
        f'Write a child-friendly rhyme about curiosity, a new {proj.thing}, and a careful grown-up saying a step is "fatal" to rush.'
    ]


def tell(proj: Project, resp: Response, child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    project = world.add(Entity(id="project", type="thing", label=proj.thing))
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["project_cfg"] = proj
    world.facts["response"] = resp

    intro(world, child, parent, proj)
    world.para()
    curiosity(world, child, proj)
    warn(world, parent, child, proj)
    redirect(world, parent, child, proj)
    world.para()
    finish(world, parent, child, proj, resp)
    world.facts["resolved"] = True
    return world


PROJECTS = {
    "lantern": Project(
        id="lantern",
        place="the hallway",
        thing="lantern",
        rhyme_a="light",
        rhyme_b="bright",
        hazard="a hot bulb",
        install_task="install a little lantern",
        safe_task="hold the screws in a tin",
        tool="the battery pack",
        outcome_line="Its glow was warm, its shine was right, and the hallway sparkled in the light.",
        tags={"install", "fatal", "curiosity", "light"},
    ),
    "birdhouse": Project(
        id="birdhouse",
        place="the porch",
        thing="birdhouse",
        rhyme_a="nest",
        rhyme_b="best",
        hazard="a wobbly ladder",
        install_task="install the birdhouse",
        safe_task="paint the birdhouse door",
        tool="the ladder",
        outcome_line="The birdhouse sat snug and high, and the sparrows sang a cheery sky-song by.",
        tags={"install", "fatal", "curiosity", "birds"},
    ),
    "smoke_alarm": Project(
        id="smoke_alarm",
        place="the kitchen",
        thing="smoke alarm",
        rhyme_a="beep",
        rhyme_b="deep",
        hazard="a live wire",
        install_task="install a smoke alarm",
        safe_task="pass the batteries along",
        tool="the wire",
        outcome_line="The alarm clicked in place just fine, and the kitchen felt safe and fine.",
        tags={"install", "fatal", "curiosity", "safety"},
    ),
}

RESPONSES = {
    "screwdriver": Response(
        id="screwdriver",
        sense=3,
        power=3,
        text="carefully tightened the last few screws and set the {thing} in place",
        fail="tried to hurry the install, but the pieces slipped out of hand",
        qa_text="carefully tightened the last few screws and set the {thing} in place",
        tags={"safe", "tool"},
    ),
    "hold_light": Response(
        id="hold_light",
        sense=3,
        power=2,
        text="held the flashlight steady while the work was done",
        fail="held the flashlight, but the job still needed more hands",
        qa_text="held the flashlight steady while the work was done",
        tags={"safe", "light"},
    ),
    "ask_first": Response(
        id="ask_first",
        sense=4,
        power=4,
        text="asked first, listened well, and helped with the calm, safe parts",
        fail="asked first, but then the child forgot and reached too soon",
        qa_text="asked first, listened well, and helped with the calm, safe parts",
        tags={"safe", "curiosity"},
    ),
    "tape_label": Response(
        id="tape_label",
        sense=2,
        power=2,
        text="put the label on straight and smiled at the tidy, finished frame",
        fail="taped the label wrong and had to start over again",
        qa_text="put the label on straight and smiled at the tidy, finished frame",
        tags={"safe", "tidy"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Rosa", "Ivy", "Nina"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Eli", "Noah"]
TRAITS = ["curious", "careful", "brave", "gentle"]

KNOWLEDGE = {
    "install": [("What does install mean?",
                 "Install means to put a thing into place so it can work. People install new parts carefully so they fit right.")],
    "curiosity": [("What is curiosity?",
                   "Curiosity is the feeling that makes you want to learn and look closer. It can help you discover things, but you still need to stay safe.")],
    "fatal": [("What does fatal mean?",
               "Fatal means something very serious that can cause death. It is a scary word, so grown-ups use it to warn about real danger.")],
    "safety": [("Why should a child ask first before helping?",
                "Asking first keeps everyone safe. A grown-up can show the right way and stop a dangerous mistake.")],
    "wire": [("Why is a live wire dangerous?",
              "A live wire can give a strong electric shock. It is not safe for children to touch.")],
    "ladder": [("Why can a ladder be dangerous?",
                "A ladder can tip or slip if it is used the wrong way. Grown-ups must hold it and use it carefully.")],
    "light": [("What is a flashlight for?",
               "A flashlight helps you see in the dark. It uses batteries, so it is safe and has no flame.")],
}
KNOWLEDGE_ORDER = ["install", "curiosity", "fatal", "safety", "wire", "ladder", "light"]


def valid_project_responses() -> list[tuple[str, str]]:
    return [(pid, rid) for pid in PROJECTS for rid in RESPONSES if RESPONSES[rid].sense >= SENSE_MIN]


def explain_rejection(resp: Response) -> str:
    return f"(No story: response {resp.id} is too weak for this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming curiosity storyworld.")
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_project_responses()
              if (args.project is None or c[0] == args.project)
              and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    project, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(project=project, response=response, child=child, child_gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS or params.response not in RESPONSES:
        raise StoryError("invalid params")
    world = tell(PROJECTS[params.project], RESPONSES[params.response], params.child, params.child_gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
response_ok(R) :- response(R), sense(R,S), sense_min(M), S >= M.
project_ok(P) :- project(P).
valid(P,R) :- project_ok(P), response_ok(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROJECTS:
        lines.append(asp.fact("project", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_project_responses()):
        print("OK: ASP matches Python valid combos.")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(StoryParams(project="lantern", response="ask_first", child="Mina", child_gender="girl", parent="mother", trait="curious"))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, r in asp_valid_combos():
            print(f"{p} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(project=pid, response="ask_first", child="Mina", child_gender="girl", parent="mother", trait="curious")) for pid in PROJECTS]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
