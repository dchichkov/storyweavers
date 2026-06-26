#!/usr/bin/env python3
"""
A heartwarming story world about a small bakery, a crooked angle, a worried
inner monologue, and a reconciliation that makes the room feel warm again.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "aunt", "sister"}
        male = {"boy", "man", "father", "dad", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bakery"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.angle: str = "crooked"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.angle = self.angle
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_slide(world: World) -> list[str]:
    out: list[str] = []
    if world.angle != "crooked":
        return out
    for actor in world.characters():
        if actor.meters["nervous"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing" or item.region != "shelf":
                continue
            sig = ("slide", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["slid"] += 1
            out.append(f"One tray wobbled on the crooked shelf.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["apology"] < THRESHOLD:
            continue
        if actor.memes["hurt"] < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] += 1
        actor.memes["hurt"] = 0.0
        out.append("__reconcile__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.kind != "thing":
            continue
        if item.meters["heated"] < THRESHOLD or item.meters["shaped"] < THRESHOLD:
            continue
        sig = ("transform", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["done"] += 1
        out.append(f"Warm dough turned into a golden bun.")
    return out


CAUSAL_RULES = [Rule("slide", _r_slide), Rule("reconcile", _r_reconcile), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__reconcile__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["slid"] >= THRESHOLD)}


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        return
    actor.meters[action.mess] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "bakery": Setting(place="the bakery", affords={"angle", "bake"}),
}

ACTIONS = {
    "angle": Action(
        id="angle",
        verb="straighten the display",
        gerund="straightening the display",
        rush="hurry to the crooked shelf",
        mess="nervous",
        soil="shaky",
        zone={"shelf"},
        keyword="angle",
        tags={"angle", "bakery"},
    ),
    "bake": Action(
        id="bake",
        verb="bake the sweet buns",
        gerund="baking sweet buns",
        rush="lean toward the oven",
        mess="warm",
        soil="golden",
        zone={"oven"},
        keyword="bakery",
        tags={"bakery", "transform"},
    ),
}

PRIZES = {
    "cake": Prize(
        label="cake",
        phrase="a little cream cake",
        type="cake",
        region="shelf",
    ),
    "pastry": Prize(
        label="pastry",
        phrase="a tray of fruit pastries",
        type="pastry",
        region="shelf",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="leveler",
        label="a small level",
        covers={"shelf"},
        guards={"nervous"},
        prep="use a small level first",
        tail="used the small level and set the tray straight",
    ),
    Gear(
        id="mitts",
        label="oven mitts",
        covers={"oven"},
        guards={"warm"},
        prep="put on oven mitts first",
        tail="put on the oven mitts and slid the pan in safely",
        plural=True,
    ),
]

NAMES = ["Maya", "Nina", "Owen", "Theo", "Lena", "Iris", "Milo", "Pia"]
TRAITS = ["gentle", "shy", "careful", "brave", "kind"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            act = ACTIONS[action]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place, action, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming bakery story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "baker"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid bakery story matches the chosen options.")
    place, action, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father", "baker"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place, action, prize, name, gender, parent, trait)


def _describe_actor(hero: Entity) -> str:
    return f"little {hero.memes.get('trait', 'kind')} {hero.type}".strip()


def tell(setting: Setting, action: Action, prize_cfg: Prize,
         hero_name: str = "Maya", hero_type: str = "girl",
         trait: str = "kind", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    hero.memes["trait"] = 1
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=parent_type))
    prize = world.add(Entity(
        id="Prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    hero.memes["calm"] += 1
    prize.worn_by = None

    world.say(f"{hero.id} worked in {setting.place} with flour on the counters and sugar in the air.")
    world.say(f"{hero.id} loved the soft smell of bread and the way every loaf could become something sweet.")
    world.say(f"{hero.id} hoped the day would be good, but {hero.pronoun('possessive')} eyes kept drifting to the {prize.label}.")

    world.para()
    world.say(f"One morning, the {prize.label} sat on a shelf at a crooked angle.")
    world.say(f"{hero.id} looked at it and whispered inside, 'If that tray slips, somebody will be sad.'")
    hero.meters["nervous"] += 1
    hero.memes["worry"] += 1

    if action.id == "angle":
        world.say(f"{hero.id} wanted to {action.verb}, but {hero.pronoun('possessive')} hands trembled.")
        if predict_mess(world, hero, action, prize.id)["soiled"]:
            world.say(f"{hero.id} thought, 'The bakery feels too small for a mistake like this.'")
    else:
        world.say(f"{hero.id} wanted to {action.verb} and make the room feel bright again.")

    world.say(f"{hero.id}'s {parent_type if parent_type != 'baker' else 'baker'} noticed the worried face and came closer.")
    world.say(f'"You do not have to fix it alone," {parent_type if parent_type != "baker" else "the baker"} said.')

    world.para()
    world.say(f"{hero.id} took a small breath and listened to the quiet in {hero.pronoun('possessive')} own head.")
    world.say(f"'I made it crooked,' {hero.id} thought, 'and now everyone will notice.'")
    world.say(f"Then {hero.id} looked up and said, 'I am sorry. I was afraid to ask for help.'")
    hero.memes["apology"] += 1
    hero.memes["hurt"] += 1

    gear = GEAR[0] if action.id == "angle" else GEAR[1]
    world.say(f"{parent_type if parent_type != 'baker' else 'the baker'} smiled kindly and handed over {gear.label}.")
    world.say(f'"Let us use {gear.prep.split(" first")[0]}," they said, and the worry in the room began to soften.')

    if action.id == "angle":
        hero.meters["nervous"] += 1
        world.angle = "straight"
        world.say(f"{hero.id} set the level on the shelf and nudged the tray until the edge looked even.")
        world.say(f"The shelf was no longer crooked; it stood straight and proud, like it had taken a deep breath.")
        hero.memes["relief"] += 1
    else:
        hero.meters["warm"] += 1
        world.say(f"{hero.id} put on the mitts and slid the pan into the oven.")
        world.say(f"Inside, the dough rose and turned into golden buns.")
        world.add(Entity(id="Dough", type="dough", label="dough"))
        world.get("Dough").meters["heated"] += 1
        world.get("Dough").meters["shaped"] += 1
        propagate(world)

    world.para()
    world.say(f"{hero.id} and {parent_type if parent_type != 'baker' else 'the baker'} laughed softly together.")
    world.say(f"'I can see it now,' {hero.id} said. 'The bakery feels nicer when we fix things side by side.'")
    world.say(f"They shared a warm bun, and the whole room seemed to glow with forgiveness and flour dust.")
    hero.memes["calm"] += 2
    hero.memes["love"] += 1

    world.facts.update(hero=hero, parent=parent, prize=prize, action=action, setting=setting, gear=gear, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, action, prize = f["hero"], f["action"], f["prize"]
    return [
        f'Write a heartwarming story about a child in a bakery who worries about a {prize.label} at an angle.',
        f"Tell a gentle story where {hero.id} thinks quietly, asks for help, and finds a kind reconciliation in the bakery.",
        f"Write a simple bakery story that turns a crooked shelf into a safe, happy place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, action = f["hero"], f["parent"], f["prize"], f["action"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel nervous at first?",
            answer=f"{hero.id} felt nervous because the {prize.label} sat at a crooked angle and {hero.id} worried it might slip.",
        ),
        QAItem(
            question=f"What did {hero.id} think about before asking for help?",
            answer=f"{hero.id} thought quietly that a mistake might make somebody sad, so {hero.id} chose to speak honestly.",
        ),
        QAItem(
            question=f"How did {hero.id} and the baker reconcile?",
            answer=f"{hero.id} apologized, the baker answered kindly, and they fixed the problem together with a small {GEAR[0].label if action.id == 'angle' else GEAR[1].label}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The crooked shelf was made straight, the worry went away, and the bakery felt warm and happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bakery?",
            answer="A bakery is a shop or kitchen where bread, buns, cakes, and other baked treats are made and sold.",
        ),
        QAItem(
            question="What does angle mean?",
            answer="An angle is the way two lines or surfaces meet, or the slant something has when it is not straight.",
        ),
        QAItem(
            question="Why does dough change in the oven?",
            answer="Dough changes in the oven because heat makes it rise, firm up, and turn into bread or buns.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  angle={world.angle}")
    return "\n".join(lines)


ASP_RULES = r"""
place(bakery).
action(angle).
action(bake).
prize(cake).
prize(pastry).
valid(bakery, angle, cake).
valid(bakery, angle, pastry).
valid(bakery, bake, cake).
valid(bakery, bake, pastry).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "bakery")]
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP and Python agree.")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


CURATED = [
    StoryParams("bakery", "angle", "cake", "Maya", "girl", "baker", "gentle"),
    StoryParams("bakery", "bake", "pastry", "Owen", "boy", "mother", "kind"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize],
                 params.name, params.gender, params.trait, params.parent)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
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
            header = f"### {p.name}: {p.action} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
