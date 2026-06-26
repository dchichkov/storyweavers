#!/usr/bin/env python3
"""
storyworlds/worlds/curiosity_reconciliation_moral_value_transformation_nursery_rhyme.py
=======================================================================================

A tiny story world in a nursery-rhyme style about curiosity, mistakes, apology,
reconciliation, and a gentle transformation.

Seed tale premise:
A curious little child (or animal friend) peeks, pokes, and wanders just a bit too
far. The curious action causes a small problem with something treasured. A wise
helper notices, the mistake is faced honestly, and the story turns toward repair:
words soften, hands help, and the world changes from messy to mended.

This world is intentionally small and constraint-checked:
- curiosity is the motivating force
- reconciliation is the emotional turn
- moral value is expressed as honesty, apology, and care
- transformation is a literal state change in a repaired object and a shifted heart
- prose aims for a child-facing nursery rhyme rhythm, without becoming a frozen template
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type == "friend":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = False
    mood: str = ""


@dataclass
class Curiosity:
    verb: str
    rush: str
    delight: str
    keyword: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mess", 0.0) < THRESHOLD:
            continue
        prize_id = world.facts.get("prize_id")
        prize = world.entities.get(prize_id)
        if not prize:
            continue
        sig = ("soil", actor.id, prize.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
        prize.meters["broken"] = prize.meters.get("broken", 0.0) + 1
        out.append(f"{prize.label_word} got dusty and bent.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("fixed"):
        return out
    fix_id = world.facts.get("fix_id")
    prize_id = world.facts.get("prize_id")
    if not fix_id or not prize_id:
        return out
    prize = world.entities[prize_id]
    if prize.meters.get("broken", 0.0) < THRESHOLD:
        return out
    sig = ("repair", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["broken"] = 0.0
    prize.meters["dirty"] = 0.0
    prize.meters["mended"] = 1.0
    world.facts["fixed"] = True
    out.append(f"The little thing was mended with care.")
    return out


CAUSAL_RULES = [Rule("soil", _r_soil), Rule("repair", _r_repair)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World, actor: Entity, curiosity: Curiosity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["mess"] = 1.0
    _do_curiosity(sim, sim.get(actor.id), curiosity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "broken": prize.meters.get("broken", 0.0) >= THRESHOLD,
        "dirty": prize.meters.get("dirty", 0.0) >= THRESHOLD,
    }


def place_detail(setting: Setting) -> str:
    return {
        "garden": "The garden gate was bright with dew.",
        "attic": "The attic was dim, with boxes stacked like sleepy hills.",
        "kitchen": "The kitchen was warm, with a table like a little stage.",
        "meadow": "The meadow was wide, where clover nodded in the sun.",
    }.get(setting.place, f"{setting.place.capitalize()} was quiet and still.")


def _do_curiosity(world: World, actor: Entity, curiosity: Curiosity, narrate: bool = True) -> None:
    actor.meters["curiosity"] = actor.meters.get("curiosity", 0.0) + 1
    actor.meters["mess"] = actor.meters.get("mess", 0.0) + 1
    actor.memes["delight"] = actor.memes.get("delight", 0.0) + 1
    world.facts["curious_action"] = curiosity.keyword
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type}, bright as a berry and quick as a bee.")


def love_question(world: World, hero: Entity, curiosity: Curiosity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved to ask and peer and peek, and listen to each tree.")


def show_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} found {hero.pronoun('possessive')} {prize.label}, neat and dear to see.")
    prize.worn_by = hero.id


def arrive(world: World, hero: Entity, helper: Entity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {helper.label_word} came softly to {world.setting.place}.")
    world.say(place_detail(world.setting))


def want_peek(world: World, hero: Entity, curiosity: Curiosity, prize: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.id} wanted to {curiosity.verb}, though {hero.pronoun('possessive')} nose was full of glee.")
    world.say(f"But {prize.label_word} was close by, and curious eyes can stray too far, you see.")


def warn(world: World, helper: Entity, hero: Entity, curiosity: Curiosity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, curiosity, prize.id)
    if not pred["broken"]:
        return False
    world.facts["predicted_broken"] = True
    world.say(f'"Mind your paws," {helper.id} said. "That trinket may not stay."')
    return True


def stray(world: World, hero: Entity, curiosity: Curiosity) -> None:
    hero.memes["impulse"] = hero.memes.get("impulse", 0.0) + 1
    world.say(f"But {hero.id} could not wait, and off {hero.pronoun()} went away.")
    world.say(f"{hero.pronoun().capitalize()} tried to {curiosity.rush}, and bumped the little display.")


def apologize(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
    hero.memes["honesty"] = hero.memes.get("honesty", 0.0) + 1
    world.say(f"Then {hero.id} bowed {hero.pronoun('possessive')} head and said, “I am sorry, and I see.”")
    world.say(f"“I chose to poke and pry too much; please help me mend it,” said {hero.id}.")


def reconcile(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0.0) + 1
    helper.memes["reconciliation"] = helper.memes.get("reconciliation", 0.0) + 1
    world.say(f"{helper.id} smiled like sunrise and took {hero.pronoun('possessive')} hand in kind.")
    world.say(f"“A true sorry is a sturdy bridge,” {helper.id} said, “and we will cross it twined.”")


def fix(world: World, helper: Entity, hero: Entity, prize: Entity, fix_def: Fix) -> None:
    world.facts["fixed"] = False
    world.say(f"They used {fix_def.label}, and {fix_def.prep}.")
    world.facts["fixed"] = True
    propagate(world, narrate=True)
    world.say(f"{fix_def.tail.capitalize()}, and the {prize.label} was bright again as new.")


def transform_closure(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["moral"] = hero.memes.get("moral", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(f"{hero.id} learned that honesty helps the heart grow light and true.")
    world.say(f"And {prize.label} changed from dented to mended, in the end, in view.")


def tell(setting: Setting, curiosity: Curiosity, prize_cfg: Prize, fix_def: Fix,
         hero_name: str = "Mina", hero_type: str = "girl", helper_name: str = "Nana",
         helper_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label="helper"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=helper.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    world.facts["prize_id"] = prize.id
    world.facts["fix_id"] = fix_def.id

    introduce(world, hero)
    love_question(world, hero, curiosity)
    show_prize(world, hero, prize)

    world.para()
    arrive(world, hero, helper)
    want_peek(world, hero, curiosity, prize)
    warn(world, helper, hero, curiosity, prize)
    stray(world, hero, curiosity)

    world.para()
    apologize(world, hero, helper)
    reconcile(world, hero, helper)
    fix(world, helper, hero, prize, fix_def)
    transform_closure(world, hero, helper, prize)

    world.facts.update(hero=hero, helper=helper, prize=prize, curiosity=curiosity, fix=fix_def)
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, mood="dew"),
    "kitchen": Setting(place="the kitchen", indoor=True, mood="warm"),
    "attic": Setting(place="the attic", indoor=True, mood="dust"),
    "meadow": Setting(place="the meadow", indoor=False, mood="sun"),
}

CURIOSITIES = {
    "jar": Curiosity(
        verb="peek into the jar",
        rush="tiptoe to the jar",
        delight="the glitter inside went wink and spark",
        keyword="jar",
        tags={"shine", "glass"},
    ),
    "book": Curiosity(
        verb="turn the tiny page",
        rush="dash to the book",
        delight="the pictures danced like bees in bark",
        keyword="book",
        tags={"book", "paper"},
    ),
    "garden": Curiosity(
        verb="follow the silver snail",
        rush="run after the snail",
        delight="the snail left a gleam behind its trail",
        keyword="snail",
        tags={"garden", "snail"},
    ),
}

PRIZES = {
    "lantern": Prize(label="lantern", phrase="a little lantern", type="lantern", region="torso"),
    "cake": Prize(label="cake", phrase="a sweet round cake", type="cake", region="hands"),
    "kite": Prize(label="kite", phrase="a bright paper kite", type="kite", region="arms"),
}

FIXES = {
    "rag": Fix(id="rag", label="a soft rag", prep="they wiped the dust away with care", tail="Soon the fix was done"),
    "glue": Fix(id="glue", label="a dab of glue", prep="they pressed the pieces together just so", tail="Soon the crack was hidden"),
    "ribbon": Fix(id="ribbon", label="a tidy ribbon", prep="they tied the loose bits neat and small", tail="Soon the bundle looked new"),
}

TRAITS = ["curious", "gentle", "brave", "cheerful"]


@dataclass
class StoryParams:
    place: str
    curiosity: str
    prize: str
    fix: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(curiosity: Curiosity, prize: Prize) -> bool:
    return True


def select_fix(curiosity: Curiosity, prize: Prize) -> Optional[Fix]:
    mapping = {
        ("jar", "lantern"): FIXES["rag"],
        ("book", "kite"): FIXES["ribbon"],
        ("garden", "cake"): FIXES["glue"],
    }
    return mapping.get((curiosity.keyword, prize.label))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for cur in CURIOSITIES:
            c = CURIOSITIES[cur]
            for prize in PRIZES:
                p = PRIZES[prize]
                if select_fix(c, p):
                    out.append((place, cur, prize))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story about curiosity, apology, and a kind fix in {world.setting.place}.',
        f"Tell a gentle story where {f['hero'].id} is curious about {f['curiosity'].keyword} and learns to say sorry.",
        f'Write a short child-friendly tale that ends with reconciliation and a transformed {f["prize"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    curiosity: Curiosity = f["curiosity"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question=f"What was {hero.id} curious about at {world.setting.place}?",
            answer=f"{hero.id} was curious about how to {curiosity.verb}. That made {hero.id} want to look very closely.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about {prize.label}?",
            answer=f"{helper.id} worried because the curious poking could make the {prize.label} dirty or bent.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} make peace again?",
            answer=f"{hero.id} said sorry, and {helper.id} answered kindly. Then they used {fix.label} to mend the problem together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {prize.label} changed from damaged to mended, and {hero.id}'s heart changed too: {hero.id} learned honesty and care.",
        ),
    ]


KNOWLEDGE = {
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, ask, and learn about something new.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had a problem make peace again and feel close once more.",
        )
    ],
    "moral": [
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of acting, like honesty, kindness, and fairness.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is transformation?",
            answer="Transformation is a change from one state to another, like broken to fixed or worried to calm.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ["curiosity", "reconciliation", "moral", "transformation"] for qa in KNOWLEDGE[key]]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", curiosity="jar", prize="lantern", fix="rag", name="Mina", gender="girl", helper="Nana", helper_gender="woman", trait="curious"),
    StoryParams(place="kitchen", curiosity="book", prize="kite", fix="ribbon", name="Pip", gender="boy", helper="Papa", helper_gender="man", trait="gentle"),
    StoryParams(place="meadow", curiosity="garden", prize="cake", fix="glue", name="Lily", gender="girl", helper="Mother", helper_gender="woman", trait="cheerful"),
]


ASP_RULES = r"""
curious(C) :- character(C), meter(C, curiosity, V), V > 0.
risk(C,P) :- curious(C), prize(P), meter(P, broken, B), B > 0.
needs_fix(C,P) :- curious(C), prize(P), fixable(C,P).

valid(Place, Cur, Prize) :- setting(Place), curiosity(Cur), prize(Prize), fixable_by(Cur, Prize).
valid_story(Place, Cur, Prize, Fix) :- valid(Place, Cur, Prize), fix(Fix), fixable_by(Cur, Prize, Fix).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for cid, c in CURIOSITIES.items():
        lines.append(asp.fact("curiosity", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
    for cur_id, c in CURIOSITIES.items():
        for prize_id, p in PRIZES.items():
            if select_fix(c, p):
                lines.append(asp.fact("fixable_by", cur_id, prize_id))
                lines.append(asp.fact("fixable_by", cur_id, prize_id, select_fix(c, p).id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_py() -> list[tuple]:
    return sorted(set(valid_combos()))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos_py())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about curiosity, reconciliation, moral value, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    combos = valid_combos_py()
    if args.place or args.curiosity or args.prize:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.curiosity is None or c[1] == args.curiosity) and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, cur_id, prize_id = rng.choice(combos)
    c = CURIOSITIES[cur_id]
    p = PRIZES[prize_id]
    fix = select_fix(c, p)
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    name = args.name or rng.choice(["Mina", "Pip", "Lily", "Theo", "Ada"])
    helper = args.helper or rng.choice(["Nana", "Papa", "Mother", "Father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, curiosity=cur_id, prize=prize_id, fix=fix.id, name=name, gender=gender, helper=helper, helper_gender=helper_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CURIOSITIES[params.curiosity], PRIZES[params.prize], FIXES[params.fix], params.name, params.gender, params.helper, params.helper_gender)
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
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, curiosity, prize) combos ({len(stories)} with fix):\n")
        for place, cur, prize in triples:
            fixes = sorted(f for (pl, cu, pr, f) in stories if (pl, cu, pr) == (place, cur, prize))
            print(f"  {place:8} {cur:10} {prize:8}  [{', '.join(fixes)}]")
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
            header = f"### {p.name}: {p.curiosity} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
