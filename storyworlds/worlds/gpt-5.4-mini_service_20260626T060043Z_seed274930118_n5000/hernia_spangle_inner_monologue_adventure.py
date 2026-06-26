#!/usr/bin/env python3
"""
storyworlds/worlds/hernia_spangle_inner_monologue_adventure.py
==============================================================

A small adventure story world about a brave child, a glittering spangle,
and a careful pause when a hernia makes heavy lifting a bad idea.

Premise:
- The hero loves adventure and dreams of carrying a sparkling spangle token
  through a little quest.
- The world tracks a physical strain meter for the hernia and a cheerful
  meme for courage.
- When the hero tries to lift or climb with the wrong load, the strain rises.
- A helper can offer a safer route so the adventure still succeeds.

Features:
- Inner monologue is part of the narrative style.
- Adventure tone: maps, quests, daring, discovery, and a clear return.
- ASP twin checks the same reasonableness gate as Python.
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
STRAIN_KEYS = {"strain", "ache"}
MEME_KEYS = {"courage", "worry", "relief", "pride"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    strain: str
    risk: str
    tags: set[str] = field(default_factory=set)
    keyword: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    weight: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route = self.route
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("strain", 0.0) < THRESHOLD:
            continue
        sig = ("strain_notice", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.pronoun('possessive').capitalize()} side felt sore, so {actor.pronoun()} slowed down.")
    return out


def _r_burden(world: World) -> list[str]:
    out: list[str] = []
    for prize in list(world.entities.values()):
        carrier = prize.carried_by
        if not carrier:
            continue
        actor = world.get(carrier)
        if actor.meters.get("strain", 0.0) < THRESHOLD:
            continue
        sig = ("burden", prize.id, actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.id} did not want to make the load worse.")
    return out


CAUSAL_RULES = [
    Rule("strain", "physical", _r_strain),
    Rule("burden", "social", _r_burden),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, task: Task) -> str:
    if setting.place == "the old bridge":
        return "Below, the river flashed like a silver ribbon."
    if setting.place == "the stone trail":
        return "The stone trail curled uphill beside a row of pines."
    return f"{setting.place.capitalize()} looked ready for a daring walk."


def task_is_risky(task: Task, prize: Prize) -> bool:
    return prize.type in task.tags or "heavy" in prize.tags and "lift" in task.tags


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if task.id in aid.helps:
            return aid
    return None


def predict_strain(world: World, actor: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "worse": bool(prize and sim.get(actor.id).meters.get("strain", 0.0) >= THRESHOLD),
        "worry": sim.get(actor.id).memes.get("worry", 0.0),
    }


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        return
    actor.meters["strain"] = actor.meters.get("strain", 0.0) + 1
    actor.memes["courage"] = actor.memes.get("courage", 0.0) + 1
    propagate(world, narrate=narrate)


def activity_opening(task: Task) -> str:
    return {
        "climb": "each step felt like a rung on a secret ladder",
        "carry": "the path felt like a quest across a map",
        "lift": "the prize gleamed like treasure in a storybook",
    }.get(task.id, "the day felt like an adventure")


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved maps, hills, and secret paths."
    )


def loves_adventure(world: World, hero: Entity, task: Task) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {task.gerund}; {activity_opening(task)}."
    )


def find_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"On a windy morning, {hero.id} found a shining {prize.label} tucked beside the trail."
    )


def inner_thought(world: World, hero: Entity, task: Task, prize: Entity) -> None:
    world.say(
        f'"I can carry this," {hero.id} thought, "and maybe the whole trail will cheer for me."'
    )


def warn(world: World, parent: Entity, hero: Entity, task: Task, prize: Entity) -> bool:
    pred = predict_strain(world, hero, task, prize.id)
    if not pred["worse"]:
        return False
    world.facts["predicted_risk"] = task.risk
    world.say(
        f'"If you push too hard, your side could hurt," {parent.pronoun().capitalize()} said. '
        f'"Let us find a safer way."'
    )
    return True


def hesitate(world: World, hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} paused. {hero.pronoun().capitalize()} did not like the idea of stopping a quest.")


def monologue(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f'"Maybe a brave explorer knows when to slow down," {hero.id} thought. '
        f'"I can still finish the journey."'
    )


def offer_aid(world: World, parent: Entity, hero: Entity, task: Task, prize: Entity) -> Optional[Aid]:
    aid = select_aid(task, prize)
    if aid is None:
        return None
    tool = world.add(Entity(
        id=aid.id,
        type="tool",
        label=aid.label,
        owner=hero.id,
        caretaker=parent.id,
        plural=aid.plural,
    ))
    tool.carried_by = hero.id
    if predict_strain(world, hero, task, prize.id)["worse"]:
        tool.carried_by = None
        del world.entities[tool.id]
        return None
    world.say(
        f'{parent.id} smiled and said, "{aid.prep}."'
    )
    return aid


def accept(world: World, hero: Entity, parent: Entity, task: Task, prize: Entity, aid: Aid) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(
        f'{hero.id} nodded, and {hero.pronoun()} felt lighter at once.'
    )
    world.say(
        f"They {aid.tail}. Soon {hero.id} was {task.gerund}, {prize.label} safe in hand, "
        f"with the trail glittering ahead like a ribbon of stars."
    )


def tell(setting: Setting, task: Task, prize_cfg: Prize,
         hero_name: str = "Mara", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"]),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    prize.tags = set(prize_cfg.tags)

    introduce(world, hero)
    loves_adventure(world, hero, task)
    find_prize(world, hero, prize)
    inner_thought(world, hero, task, prize)

    world.para()
    world.say(setting_detail(setting, task))
    world.say(f"{hero.id} wanted to {task.verb}, but the {prize.label} looked too important to risk.")
    warn(world, parent, hero, task, prize)
    hesitate(world, hero)
    monologue(world, hero, task)

    world.para()
    aid = offer_aid(world, parent, hero, task, prize)
    if aid:
        accept(world, hero, parent, task, prize, aid)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       task=task, setting=setting, aid=aid)
    return world


SETTINGS = {
    "hill": Setting(place="the hill", outdoors=True, affords={"climb", "carry"}),
    "bridge": Setting(place="the old bridge", outdoors=True, affords={"carry"}),
    "trail": Setting(place="the stone trail", outdoors=True, affords={"carry", "lift"}),
}

TASKS = {
    "climb": Task(
        id="climb",
        verb="climb the hill",
        gerund="climbing hills",
        rush="dash up the hill",
        strain="strained from climbing",
        risk="strain",
        tags={"climb", "lift", "heavy"},
        keyword="hill",
    ),
    "carry": Task(
        id="carry",
        verb="carry the spangle token",
        gerund="carrying treasure",
        rush="run with the token",
        strain="strained from carrying",
        risk="strain",
        tags={"carry", "lift", "heavy"},
        keyword="spangle",
    ),
    "lift": Task(
        id="lift",
        verb="lift the spangle chest",
        gerund="lifting treasure",
        rush="hoist the chest high",
        strain="strained from lifting",
        risk="strain",
        tags={"lift", "heavy"},
        keyword="spangle",
    ),
}

PRIZES = {
    "spangle": Prize(
        label="spangle token",
        phrase="a bright spangle token",
        type="spangle",
        weight="light",
        tags={"spangle"},
    ),
    "chest": Prize(
        label="spangle chest",
        phrase="a small spangle chest",
        type="chest",
        weight="heavy",
        tags={"spangle", "heavy"},
    ),
    "satchel": Prize(
        label="spangle satchel",
        phrase="a glittery spangle satchel",
        type="satchel",
        weight="heavy",
        tags={"spangle", "heavy"},
    ),
}

AIDS = [
    Aid(
        id="cart",
        label="a little cart",
        prep="Let's use a little cart so the treasure can roll instead of being lifted",
        tail="rolled the treasure along the trail together",
        helps={"carry", "lift", "climb"},
    ),
    Aid(
        id="rope",
        label="a hand rope",
        prep="Hold this hand rope, and I will help guide the load",
        tail="walked carefully with the rope steady between them",
        helps={"carry"},
    ),
]

GIRL_NAMES = ["Mara", "Lina", "Tessa", "Nina", "Ivy", "Ruby"]
BOY_NAMES = ["Arlo", "Jasper", "Finn", "Theo", "Owen", "Milo"]
TRAITS = ["brave", "curious", "spirited", "bold", "quick", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for prize_id, prize in PRIZES.items():
                if task_is_risky(task, prize) and select_aid(task, prize):
                    combos.append((place, task_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "spangle": [("What is a spangle?", "A spangle is a tiny shiny piece that glitters like a star.")],
    "hernia": [("What is a hernia?", "A hernia is a sore bulge in the body that can hurt if a person strains too hard.")],
    "cart": [("What is a cart for?", "A cart helps carry something heavy so a person does not have to lift it by hand.")],
    "trail": [("What is a trail?", "A trail is a path outdoors that people can follow through a park, hill, or woods.")],
    "lift": [("Why should someone be careful when lifting something heavy?", "Heavy lifting can strain the body and make a sore place hurt more.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child about a brave explorer who finds "{f["prize_cfg"].label}".',
        f"Tell a story where {f['hero'].id} wants to {f['task'].verb} but must listen to a parent because of a hernia.",
        f'Write a gentle adventure with an inner monologue and the word "spangle" that ends with a safer plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, task = f["hero"], f["parent"], f["prize"], f["task"]
    trait = next((t for t in hero.traits if t != "little"), "brave")
    qa = [
        QAItem(
            question=f"Who is the adventure about?",
            answer=f"It is about {hero.id}, a little {trait} {hero.type}, and {hero.pronoun('possessive')} {parent.type}.",
        ),
        QAItem(
            question=f"What shiny thing did {hero.id} find?",
            answer=f"{hero.id} found {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did the parent worry when {hero.id} wanted to {task.verb}?",
            answer=f"The parent worried because a hernia could hurt more if {hero.id} strained too hard.",
        ),
    ]
    if f.get("aid"):
        aid = f["aid"]
        qa.append(
            QAItem(
                question=f"How did {aid.label} help the adventure end well?",
                answer=f"It let {hero.id} keep going without having to do the heavy work alone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["task"].tags)
    tags.add("hernia")
    tags.add("spangle")
    if f.get("aid"):
        tags.add(f["aid"].id)
    out: list[QAItem] = []
    for tag in ["spangle", "hernia", "cart", "trail", "lift"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", task="carry", prize="spangle", name="Mara", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="bridge", task="carry", prize="chest", name="Arlo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="trail", task="lift", prize="satchel", name="Tessa", gender="girl", parent="mother", trait="spirited"),
]


def explain_rejection(task: Task, prize: Prize) -> str:
    return f"(No story: {task.verb} and {prize.label} do not fit the safe adventure rule for this world.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: the chosen {PRIZES[prize_id].label} does not fit the requested gender in this world.)"


ASP_RULES = r"""
task_risky(T,P) :- task(T), prize(P), task_tag(T,K), prize_tag(P,K), risky_tag(K).
needs_aid(T,P) :- task_risky(T,P), aid_for(T,A), helps(A,T).

valid_story(Place,T,P,G) :- affords(Place,T), task_risky(T,P), needs_aid(T,P), wears(G,P).
valid_combo(Place,T,P) :- affords(Place,T), task_risky(T,P), needs_aid(T,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("prize_tag", pid, tag))
        lines.append(asp.fact("wears", "girl", pid))
        lines.append(asp.fact("wears", "boy", pid))
    for aid in AIDS:
        lines.append(asp.fact("aid_for", aid.id, *sorted(aid.helps)[0:1]))
        for t in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.id, t))
    lines.append(asp.fact("risky_tag", "heavy"))
    lines.append(asp.fact("risky_tag", "lift"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with a hernia, a spangle, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.task and args.prize:
        task, prize = TASKS[args.task], PRIZES[args.prize]
        if not (task_is_risky(task, prize) and select_aid(task, prize)):
            raise StoryError(explain_rejection(task, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "adventurous"], params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, task, prize) combos ({len(stories)} with gender):\n")
        for place, task, prize in triples:
            genders = sorted(g for (pl, ta, pr, g) in stories if (pl, ta, pr) == (place, task, prize))
            print(f"  {place:10} {task:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
