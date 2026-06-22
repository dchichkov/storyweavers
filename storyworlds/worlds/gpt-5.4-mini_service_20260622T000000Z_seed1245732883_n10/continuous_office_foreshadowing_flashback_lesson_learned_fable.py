#!/usr/bin/env python3
"""
storyworlds/worlds/continuous_office_foreshadowing_flashback_lesson_learned_fable.py
====================================================================================

A tiny fable-style office story world built around a continuous problem,
a foreshadowed warning, a flashback to an earlier mistake, and a lesson learned.

The domain is small on purpose: an office animal notices a repeating trouble,
remembers a past slip, predicts the consequence, and chooses a wiser way.
Every story is driven by world state rather than by swapping nouns in a template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "she", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"cat", "he", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class OfficeSetting:
    id: str
    label: str
    signal: str
    path: str
    helper: str


@dataclass
class Trouble:
    id: str
    label: str
    repeated_sign: str
    hidden_cause: str
    risk: str
    lesson: str


@dataclass
class Response:
    id: str
    label: str
    method: str
    power: int
    sense: int
    qa: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        ent.meters = dict(ent.meters)
        ent.memes = dict(ent.memes)
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


OFFICES = {
    "quiet": OfficeSetting(id="quiet", label="a quiet office", signal="paper rustling", path="the hallway", helper="the clerk"),
    "bright": OfficeSetting(id="bright", label="a bright office", signal="printer humming", path="the supply room", helper="the manager"),
    "evening": OfficeSetting(id="evening", label="an evening office", signal="lamp glow", path="the mail desk", helper="the janitor"),
}

TROUBLES = {
    "draft": Trouble(
        id="draft",
        label="a cold draft",
        repeated_sign="the papers kept fluttering off the desk",
        hidden_cause="an open window",
        risk="the ink pages could scatter",
        lesson="close the window when the wind keeps sneaking in",
    ),
    "drip": Trouble(
        id="drip",
        label="a steady drip",
        repeated_sign="drop after drop fell into the same little cup",
        hidden_cause="a ceiling leak",
        risk="the floor could become slick",
        lesson="put a cup under the leak and tell a grown-up",
    ),
    "jam": Trouble(
        id="jam",
        label="a printer jam",
        repeated_sign="the printer kept coughing and blinking red",
        hidden_cause="too many pages at once",
        risk="the letters could not leave on time",
        lesson="clear the papers one calm stack at a time",
    ),
}

RESPONSES = {
    "notice": Response("notice", "notice the pattern", "look closely and call for help", 3, 3, "looked closely and called for help"),
    "fix": Response("fix", "fix the problem gently", "do the safe fix right away", 2, 4, "did the safe fix right away"),
    "wait": Response("wait", "wait and watch", "watch the pattern before acting", 1, 1, "watched and waited, but that was not enough"),
}

GENDER_NAMES = {
    "mouse": ["Milo", "Mina", "Nia", "Pip", "Tessa"],
    "cat": ["Cleo", "Morris", "Mika", "Toby"],
}


@dataclass
class StoryParams:
    office: str
    trouble: str
    response: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(office="quiet", trouble="draft", response="notice", hero_name="Mina", hero_type="mouse", helper_name="Clerk", helper_type="cat", seed=1),
    StoryParams(office="bright", trouble="drip", response="fix", hero_name="Pip", hero_type="mouse", helper_name="Manager", helper_type="cat", seed=2),
    StoryParams(office="evening", trouble="jam", response="fix", hero_name="Tessa", hero_type="mouse", helper_name="Janitor", helper_type="cat", seed=3),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for oid in OFFICES:
        for tid in TROUBLES:
            for rid, r in RESPONSES.items():
                if r.sense >= 2:
                    combos.append((oid, tid, rid))
    return combos


def hazard_label(trouble: Trouble) -> str:
    return trouble.label


def predict_consequence(world: World, trouble_id: str) -> dict:
    trouble = TROUBLES[trouble_id]
    sim = world.copy()
    hero = sim.get("hero")
    if trouble_id == "draft":
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        sim.get("office").meters["mess"] = sim.get("office").meters.get("mess", 0) + 1
    elif trouble_id == "drip":
        sim.get("office").meters["wet"] = sim.get("office").meters.get("wet", 0) + 1
    else:
        sim.get("office").meters["delay"] = sim.get("office").meters.get("delay", 0) + 1
    return {"risk": trouble.risk, "repeat": True}


def build_story(world: World, office: OfficeSetting, trouble: Trouble, response: Response) -> None:
    hero = world.add(Entity(id="hero", kind="character", type=world.facts["hero_type"], role="observer", traits=["careful"], meters={"worry": 0.0}, memes={"curiosity": 1.0, "worry": 0.0, "hope": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=world.facts["helper_type"], role="helper", traits=["wise"], meters={}, memes={"calm": 1.0}))
    room = world.add(Entity(id="office", kind="place", type="office", label=office.label, meters={"mess": 0.0, "wet": 0.0, "delay": 0.0}))
    world.facts["office"] = office
    world.facts["trouble"] = trouble
    world.facts["response"] = response

    world.say(
        f"In {office.label}, {hero.id} noticed {office.signal}. "
        f"It was a continuous sign that something was not quite right."
    )
    world.say(
        f"{trouble.repeated_sign} {hero.id} frowned, because the office had seen this before."
    )

    world.para()
    hero.memes["worry"] += 1
    world.say(
        f"Then came a flashback: once, {hero.id} had ignored the sign and made a larger mess. "
        f"That memory came back like a small bell, and {hero.pronoun()} remembered the trouble."
    )

    pred = predict_consequence(world, trouble.id)
    world.facts["predicted"] = pred["risk"]
    world.say(
        f"So {hero.id} spoke at once: {response.label}. "
        f"{hero.pronoun().capitalize()} knew the sign could lead to {pred['risk']} if nobody acted."
    )

    world.para()
    if response.id == "wait":
        room.meters["mess"] += 1
        world.say(
            f"{helper.id} shook {helper.pronoun('possessive')} head and stepped in. "
            f"{helper.id} did not like waiting when the danger was already plain."
        )
        world.say(
            f"Together they chose the wiser way: {response.method}. "
            f"{helper.id} helped with calm hands, and the office settled down."
        )
    elif response.id == "notice":
        if trouble.id == "draft":
            room.meters["mess"] += 1
            world.say(
                f"{helper.id} found the open window and closed it. The papers stopped flying, "
                f"and the office grew still again."
            )
        elif trouble.id == "drip":
            room.meters["wet"] += 1
            world.say(
                f"{helper.id} put a cup under the drip and sent for help. The floor stayed safe, "
                f"and the little drip became only a quiet sound."
            )
        else:
            room.meters["delay"] += 1
            world.say(
                f"{helper.id} cleared the jam one stack at a time. The printer sighed, then worked again."
            )
    else:
        if trouble.id == "draft":
            world.say(
                f"{helper.id} closed the window and held the pages flat. The wind lost its game."
            )
        elif trouble.id == "drip":
            world.say(
                f"{helper.id} set the cup in place and wiped the floor dry. The slick spot was gone."
            )
        else:
            world.say(
                f"{helper.id} gently cleared the printer and fed the pages back in the right order. "
                f"The letters marched out at last."
            )

    world.para()
    hero.memes["hope"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"From then on, {hero.id} kept the lesson learned close: "
        f"{trouble.lesson}. In the office, a little wisdom can prevent a lot of trouble."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        room=room,
        outcome="wise",
        lesson=trouble.lesson,
    )


def tell(params: StoryParams) -> World:
    if params.office not in OFFICES or params.trouble not in TROUBLES or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    office = OFFICES[params.office]
    trouble = TROUBLES[params.trouble]
    response = RESPONSES[params.response]
    world = World()
    world.facts["hero_name"] = params.hero_name
    world.facts["helper_name"] = params.helper_name
    world.facts["hero_type"] = params.hero_type
    world.facts["helper_type"] = params.helper_type
    build_story(world, office, trouble, response)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    office = f["office"]
    trouble = f["trouble"]
    return [
        f'Write a fable-style story that includes the words "continuous" and "office".',
        f"Tell a short lesson story about {f['hero_name']} in {office.label} noticing {trouble.repeated_sign} and learning what to do.",
        f"Write a child-friendly office fable with a flashback to an earlier mistake and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    office = f["office"]
    trouble = f["trouble"]
    response = f["response"]
    return [
        QAItem(
            question=f"What did {hero.id} notice in {office.label}?",
            answer=f"{hero.id} noticed {trouble.repeated_sign}. That was a continuous sign that the office needed attention.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the earlier mistake?",
            answer=f"{hero.id} had a flashback to an older time when ignoring the sign made a bigger mess. That memory helped {hero.pronoun()} choose better this time.",
        ),
        QAItem(
            question=f"What did {helper.id} do to help in the end?",
            answer=f"{helper.id} {response.qa} and made the office safe again. The helper's calm work finished the problem instead of letting it grow.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{trouble.lesson.capitalize()}. The office trouble was small at first, so noticing it early mattered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an office?",
            answer="An office is a place where people work at desks, sort papers, and solve little problems together.",
        ),
        QAItem(
            question="What does continuous mean?",
            answer="Continuous means something keeps going again and again without stopping.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory of something that happened before the present moment. It helps explain why a character acts the way they do.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand a better choice after seeing what went wrong. Then the character does things more wisely next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    out.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(out)


ASP_RULES = r"""
office(quiet). office(bright). office(evening).
trouble(draft). trouble(drip). trouble(jam).
response(notice). response(fix).
valid(O,T,R) :- office(O), trouble(T), response(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for o in OFFICES:
        lines.append(asp.fact("office", o))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-style office story world.")
    ap.add_argument("--office", choices=OFFICES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", choices=["mouse", "cat"])
    ap.add_argument("--helper-type", choices=["mouse", "cat"])
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
    combos = [c for c in valid_combos()
              if (args.office is None or c[0] == args.office)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    office, trouble, response = rng.choice(sorted(combos))
    hero_type = args.hero_type or "mouse"
    helper_type = args.helper_type or ("cat" if hero_type == "mouse" else "mouse")
    hero_name = args.name or rng.choice(GENDER_NAMES[hero_type])
    helper_name = args.helper_name or rng.choice(GENDER_NAMES[helper_type])
    return StoryParams(
        office=office,
        trouble=trouble,
        response=response,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.office not in OFFICES or params.trouble not in TROUBLES or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = World()
    world.facts["hero_name"] = params.hero_name
    world.facts["helper_name"] = params.helper_name
    world.facts["hero_type"] = params.hero_type
    world.facts["helper_type"] = params.helper_type
    build_story(world, OFFICES[params.office], TROUBLES[params.trouble], RESPONSES[params.response])
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
        print("\n".join(f"{o} {t} {r}" for o, t, r in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
