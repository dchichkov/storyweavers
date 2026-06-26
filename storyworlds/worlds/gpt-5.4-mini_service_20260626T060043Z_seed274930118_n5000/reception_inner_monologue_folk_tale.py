#!/usr/bin/env python3
"""
storyworlds/worlds/reception_inner_monologue_folk_tale.py
==========================================================

A small story world about a village reception, with folk-tale cadence and
visible inner monologue driving the turn from worry to welcome.

Premise:
- A child helper must prepare for a reception in the village hall.
- One important bowl of honey cakes is too plain, one ribbon is too short,
  and the lantern table feels unfinished.

Tension:
- The helper worries that the guests will arrive before the room feels ready.
- Their inner monologue keeps repeating the same fear: "What if the reception
  looks bare and the family feels ashamed?"

Turn:
- The helper notices a forgotten bundle of wildflowers and a long cloth.
- They use what the village already has: flowers, cloth, and warm hands.

Resolution:
- The reception becomes bright and welcoming.
- The helper's worry softens into pride, and the room proves that small work
  can become a beautiful celebration.

World model:
- Entities have physical meters (for things like neatness, fullness, brightness)
  and emotional memes (for worry, hope, pride, belonging).
- Inner monologue is not a static label; it changes with the simulated state.
- The narration is driven by what the helper sees, remembers, and decides.

Contract notes:
- This script is standalone and uses only stdlib plus storyworlds/results.py.
- storyworlds/asp.py is imported lazily inside ASP helpers only.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def em(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Hall:
    place: str = "the village hall"
    season: str = "autumn"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"set_tables", "hang_lanterns", "serve_reception"})
    brightness: float = 0.0
    neatness: float = 0.0
    welcome: float = 0.0


@dataclass
class ReceptionTask:
    id: str
    verb: str
    gerund: str
    noise: str
    effect: str
    needed: str
    tag: str = ""


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    type: str
    use: str
    fits: set[str] = field(default_factory=set)
    preferred: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    action: str
    outcome: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, hall: Hall) -> None:
        self.hall = hall
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.targeted_task: Optional[str] = None

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        c = World(copy.deepcopy(self.hall))
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.lines = [[]]
        c.targeted_task = self.targeted_task
        return c


TASKS = {
    "set_tables": ReceptionTask(
        id="set_tables",
        verb="set the long tables",
        gerund="setting the long tables",
        noise="bare",
        effect="made the room look ready",
        needed="cloth",
        tag="table",
    ),
    "hang_lanterns": ReceptionTask(
        id="hang_lanterns",
        verb="hang the lanterns",
        gerund="hanging the lanterns",
        noise="dark",
        effect="made the room glow",
        needed="light",
        tag="lantern",
    ),
    "serve_reception": ReceptionTask(
        id="serve_reception",
        verb="serve the reception food",
        gerund="serving the reception food",
        noise="hungry",
        effect="filled the room with warmth",
        needed="cakes",
        tag="food",
    ),
}

GIFTS = {
    "wildflowers": Gift(
        id="wildflowers",
        label="bundle of wildflowers",
        phrase="a fragrant bundle of wildflowers",
        type="flowers",
        use="brighten the tables",
        fits={"table", "welcome"},
    ),
    "cloth": Gift(
        id="cloth",
        label="long cloth",
        phrase="a long woven cloth",
        type="cloth",
        use="cover the tables",
        fits={"table"},
    ),
    "cakes": Gift(
        id="cakes",
        label="honey cakes",
        phrase="a tray of honey cakes",
        type="cakes",
        use="feed the guests",
        fits={"food", "welcome"},
        preferred={"girl", "boy"},
    ),
    "lanterns": Gift(
        id="lanterns",
        label="paper lanterns",
        phrase="a string of paper lanterns",
        type="lanterns",
        use="light the hall",
        fits={"lantern", "welcome"},
        preferred={"girl", "boy"},
    ),
}

FIXES = [
    Fix(id="flowers", label="wildflowers", action="gather the wildflowers from the lane", outcome="the tables looked less bare", helps={"table", "welcome"}),
    Fix(id="cloth", label="the long cloth", action="lay the long cloth across the tables", outcome="the tables looked dressed for guests", helps={"table"}),
    Fix(id="lanterns", label="the paper lanterns", action="hang the paper lanterns near the beams", outcome="the hall began to glow", helps={"lantern", "welcome"}),
]


@dataclass
class StoryParams:
    place: str = "the village hall"
    task: str = "set_tables"
    gift: str = "cloth"
    name: str = "Mira"
    gender: str = "girl"
    elder: str = "aunt"
    trait: str = "careful"
    seed: Optional[int] = None


NAMES_GIRL = ["Mira", "Anya", "Sela", "Tarin", "Lina", "Rosa", "Iva", "Nora"]
NAMES_BOY = ["Oren", "Pavel", "Milo", "Tomas", "Evan", "Rurik", "Niko", "Bram"]
TRAITS = ["careful", "bright-eyed", "quiet", "brave", "kind", "steady"]


def helper_pronoun(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in ["the village hall"]:
        for task_id, task in TASKS.items():
            for gift_id, gift in GIFTS.items():
                if task.tag in gift.fits:
                    combos.append((place, task_id, gift_id))
    return combos


def reason_gate(task: ReceptionTask, gift: Gift) -> bool:
    return task.tag in gift.fits


def explain_rejection(task: ReceptionTask, gift: Gift) -> str:
    return (
        f"(No story: {gift.label} does not honestly help with {task.gerund}. "
        f"The tale needs a fix that can actually make the reception better.)"
    )


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_brighten(world: World) -> list[str]:
    out = []
    if world.hall.brightness >= THRESHOLD:
        return out
    if world.targeted_task == "hang_lanterns":
        sig = ("brighten",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.hall.brightness += 1
        out.append("The lantern light climbed up the walls.")
    return out


def _r_neaten(world: World) -> list[str]:
    out = []
    if world.hall.neatness >= THRESHOLD:
        return out
    if world.targeted_task == "set_tables":
        sig = ("neaten",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.hall.neatness += 1
        out.append("The tables stopped looking bare.")
    return out


def _r_welcome(world: World) -> list[str]:
    out = []
    if world.hall.welcome >= THRESHOLD:
        return out
    if world.hall.brightness >= THRESHOLD and world.hall.neatness >= THRESHOLD:
        sig = ("welcome",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.hall.welcome += 1
        out.append("The room felt ready to greet the whole village.")
    return out


RULES = [Rule("brighten", _r_brighten), Rule("neaten", _r_neaten), Rule("welcome", _r_welcome)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for line in out:
            world.say(line)
    return out


def predict(world: World, helper: Entity, task: ReceptionTask, gift_id: str) -> dict:
    sim = world.copy()
    do_task(sim, sim.get(helper.id), task, gift_id, narrate=False)
    return {
        "bright": sim.hall.brightness >= THRESHOLD,
        "neat": sim.hall.neatness >= THRESHOLD,
        "welcome": sim.hall.welcome >= THRESHOLD,
    }


def inner_monologue(hero: Entity, hall: Hall, task: ReceptionTask) -> str:
    if hall.welcome >= THRESHOLD:
        return f"{hero.pronoun('subject').capitalize()} thought, 'The hall can smile now.'"
    if hall.brightness < THRESHOLD and hall.neatness < THRESHOLD:
        return f"{hero.pronoun('subject').capitalize()} thought, 'If I do nothing, the reception will look bare and sad.'"
    if hall.brightness < THRESHOLD:
        return f"{hero.pronoun('subject').capitalize()} thought, 'The room has shape, but it still needs light.'"
    return f"{hero.pronoun('subject').capitalize()} thought, 'One more honest task and the guests will feel welcome.'"


def do_task(world: World, hero: Entity, task: ReceptionTask, gift_id: str, narrate: bool = True) -> None:
    world.targeted_task = task.id
    if gift_id == "cloth" and task.id == "set_tables":
        world.hall.neatness += 1
    elif gift_id == "lanterns" and task.id == "hang_lanterns":
        world.hall.brightness += 1
    elif gift_id == "wildflowers" and task.id == "set_tables":
        world.hall.neatness += 1
        world.hall.welcome += 0.5
    elif gift_id == "cakes" and task.id == "serve_reception":
        world.hall.welcome += 1
    hero.memes["duty"] = hero.memes.get("duty", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    if narrate:
        world.say(f"{hero.id} began {task.gerund}.")
    propagate(world, narrate=narrate)


def tell(place: Hall, task: ReceptionTask, gift: Gift, name: str, gender: str, trait: str, elder: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"worry": 1.0}))
    elder_ent = world.add(Entity(id="Elder", kind="character", type=elder, label=f"the {elder}"))
    present = world.add(Entity(id=gift.id, type=gift.type, label=gift.label, phrase=gift.phrase, owner=hero.id))

    world.say(f"{name} was a {trait} child who helped at the village hall whenever a reception was near.")
    world.say(f"{name} had {gift.phrase}, and {name} meant to use it well.")
    world.para()
    world.say(f"On the day of the reception, {name} walked into {place.place} and looked around.")
    world.say(inner_monologue(hero, place, task))
    world.say(f"The {elder} whispered that the guests were on the road.")
    if task.id == "set_tables":
        world.say(f"The tables were still bare, and the cloth had not been laid.")
    elif task.id == "hang_lanterns":
        world.say(f"The beams waited in the dimness, and no lanterns yet shone there.")
    else:
        world.say(f"The warm food was not yet set out, and the room smelled only of waiting.")

    world.para()
    world.say(f"{name} wanted to {task.verb}, but the work felt larger than a small pair of hands.")
    pred = predict(world, hero, task, present.id)
    if pred["welcome"]:
        world.say(f"{name} knew the task could be finished if {hero.pronoun('subject')} stayed steady.")
    else:
        world.say(inner_monologue(hero, place, task))
    do_task(world, hero, task, present.id, narrate=True)

    if gift_id_effects(task, gift):
        world.say(f"{name} used {gift.label} to {gift.use}.")
    else:
        world.say(f"{name} looked again and found a kinder way to use what was already there.")
    world.para()
    if world.hall.welcome >= THRESHOLD:
        hero.memes["pride"] = hero.memes.get("pride", 0) + 1
        hero.memes["worry"] = 0
        world.say(f"When the last piece was set, {name} felt the worry leave like mist after sunrise.")
        world.say(f"The reception glowed, and the elder smiled at the brave little helper.")
        world.say(f"{name} thought, 'Now the village can come in, warm and glad.'")
    else:
        world.say(f"{name} kept working until the room looked right enough for guests.")
    world.facts.update(
        hero=hero,
        elder=elder_ent,
        gift=present,
        task=task,
        hall=place,
        resolved=world.hall.welcome >= THRESHOLD,
    )
    return world


def gift_id_effects(task: ReceptionTask, gift: Gift) -> bool:
    return task.tag in gift.fits


SETTINGS = {
    "hall": Hall(),
}

CURATED = [
    StoryParams(task="set_tables", gift="cloth", name="Mira", gender="girl", elder="aunt", trait="careful"),
    StoryParams(task="hang_lanterns", gift="lanterns", name="Oren", gender="boy", elder="uncle", trait="bright-eyed"),
    StoryParams(task="serve_reception", gift="cakes", name="Sela", gender="girl", elder="grandmother", trait="steady"),
]


KNOWLEDGE = {
    "reception": [
        QAItem(
            question="What is a reception?",
            answer="A reception is a gathering where people welcome guests and share food, talk, and joy after an important event.",
        )
    ],
    "lantern": [
        QAItem(
            question="What do lanterns do in a room?",
            answer="Lanterns give light and help a room feel bright and warm when evening comes.",
        )
    ],
    "flowers": [
        QAItem(
            question="Why do people bring flowers to a celebration?",
            answer="People bring flowers because they look cheerful and make a place feel special and welcoming.",
        )
    ],
    "food": [
        QAItem(
            question="Why is food important at a celebration?",
            answer="Food helps guests feel cared for, because sharing a meal is one way people show kindness.",
        )
    ],
}


def valid_story(task: ReceptionTask, gift: Gift) -> bool:
    return reason_gate(task, gift)


ASP_RULES = r"""
task_tag(set_tables, table).
task_tag(hang_lanterns, lantern).
task_tag(serve_reception, food).

gift_fits(wildflowers, table).
gift_fits(wildflowers, welcome).
gift_fits(cloth, table).
gift_fits(lanterns, lantern).
gift_fits(lanterns, welcome).
gift_fits(cakes, food).
gift_fits(cakes, welcome).

valid(Task, Gift) :- task_tag(Task, Tag), gift_fits(Gift, Tag).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_tag", tid, t.tag))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for f in sorted(g.fits):
            lines.append(asp.fact("gift_fits", gid, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(t, g) for t, task in TASKS.items() for g, gift in GIFTS.items() if valid_story(task, gift)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_story() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task = f["hero"], f["task"]
    return [
        f'Write a short folk tale about a child named {hero.id} helping at {f["hall"].place} for a reception.',
        f"Tell a gentle story where {hero.id} thinks quietly while preparing to {task.verb}.",
        f"Write a child-friendly tale with inner monologue, a village hall, and a reception that grows from worry into welcome.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, task, hall = f["hero"], f["elder"], f["task"], f["hall"]
    qa = [
        QAItem(
            question=f"What was {hero.id} helping with in the village hall?",
            answer=f"{hero.id} was helping with the reception at {hall.place}, and {hero.id} worked on {task.gerund}.",
        ),
        QAItem(
            question=f"What did {hero.id} worry about before the guests arrived?",
            answer=f"{hero.id} worried that the reception would look bare or unfinished, but {hero.id} kept working anyway.",
        ),
        QAItem(
            question=f"Who was smiling at the end of the story?",
            answer=f"The {elder.type} smiled because the room became welcoming and the reception felt ready for guests.",
        ),
    ]
    if f["resolved"]:
        qa.append(
            QAItem(
                question=f"How did the room change by the end?",
                answer=f"The hall became bright and neat, so the reception felt warm and ready to greet the village.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    if "reception" in world.story_tags():
        out.extend(KNOWLEDGE["reception"])
    if world.facts["task"].tag == "lantern":
        out.extend(KNOWLEDGE["lantern"])
    if world.facts["gift"].id == "wildflowers":
        out.extend(KNOWLEDGE["flowers"])
    if world.facts["task"].tag == "food":
        out.extend(KNOWLEDGE["food"])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"hall.brightness={world.hall.brightness} hall.neatness={world.hall.neatness} hall.welcome={world.hall.welcome}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale reception storyworld with inner monologue.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["aunt", "uncle", "grandmother", "grandfather"])
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
    if args.task and args.gift:
        if not valid_story(TASKS[args.task], GIFTS[args.gift]):
            raise StoryError(explain_rejection(TASKS[args.task], GIFTS[args.gift]))
    combos = [c for c in valid_combos()
              if (args.task is None or c[1] == args.task)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid reception tale matches the given options.)")
    place, task_id, gift_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    elder = args.elder or rng.choice(["aunt", "uncle", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, gift=gift_id, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["hall"], TASKS[params.task], GIFTS[params.gift], params.name, params.gender, params.trait, params.elder)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid (task, gift) combos:\n")
        for t, g in vals:
            print(f"  {t:16} {g}")
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} with {p.gift}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
