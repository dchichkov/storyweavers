#!/usr/bin/env python3
"""
storyworlds/worlds/faculty_udder_perspective_rhyme_animal_story.py
===================================================================

A small animal-school storyworld about a calf, a rhyme day, and the
careful point of view that helps everyone understand the problem.

Seed tale used to shape the world:
---
At the little animal school, the faculty planned a rhyme day. A young calf
named Millie loved rhymes, but she also had a very full udder and kept
worrying that everyone would stare. Her teacher, Mrs. Finch, asked her to
try the rhyme from a kinder perspective: not as a mistake, but as a silly
thing that made the class smile.

Millie took a breath, stepped onto the rug, and spoke her rhyme. The class
clapped. From that perspective, the udder was just part of being a cow, and
the faculty loved the brave little performance.
---

World shape:
- A young animal wants to perform a rhyme at school.
- The faculty member notices a worry, names it gently, and offers a shift in
  perspective.
- The performance succeeds because the child changes what she thinks the
  moment means.

This script keeps the domain small and concrete: a calf, a teacher, a rhyme,
and a school setting. The emotional turn is driven by perspective, and the
physical details are grounded in the school stage, the rug, and the calf's
body language.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Lazy import of asp happens inside helper functions only.

THRESHOLD = 1.0


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "cow", "heifer", "mother", "teacher"}
        male = {"boy", "bull", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the school barn"
    affords: set[str] = field(default_factory=set)
    audience: str = "the class"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    venue: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    worn_region: str = "neck"
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    protects_perspective: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.story_view: str = "calm"
        self.stage: str = "classroom"

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
        clone.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes))
                          for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.story_view = self.story_view
        clone.stage = self.stage
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _boost(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _feel(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _r_stage(world: World) -> list[str]:
    out = []
    if world.stage == "stage":
        for c in world.characters():
            if c.memes.get("fear", 0) >= THRESHOLD and ("stage_fear", c.id) not in world.fired:
                world.fired.add(("stage_fear", c.id))
                _feel(c, "smallness", 1)
                out.append(f"{c.id} felt tiny looking at the bright rug.")
    return out


CAUSAL_RULES = [(_r_stage)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} at {world.setting.place} who loved gentle rhymes."
    )


def faculty_note(world: World, faculty: Entity) -> None:
    world.say(
        f"{faculty.label} was part of the faculty, and {faculty.pronoun()} liked keeping the class kind and calm."
    )


def love_rhyme(world: World, hero: Entity, activity: Activity) -> None:
    _feel(hero, "love", 1)
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because the words sounded like little bells."
    )


def buy_prize(world: World, faculty: Entity, hero: Entity, prize: Prize) -> None:
    world.say(
        f"{faculty.label} brought {hero.pronoun('object')} {prize.phrase} for rhyme day."
    )


def wear_prize(world: World, hero: Entity, prize: Prize) -> None:
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} with a proud smile."
    )


def arrive(world: World, hero: Entity, faculty: Entity, activity: Activity) -> None:
    world.stage = "stage"
    world.say(
        f"One school morning, {hero.id} and {hero.pronoun('possessive')} {faculty.label} walked to {world.setting.place}."
    )
    world.say("The rug on the little stage waited in a neat square, and the class sat in a soft row.")
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the bright stage made {hero.pronoun('object')} think about {hero.pronoun('possessive')} udder."
    )


def worry(world: World, hero: Entity, faculty: Entity, prize: Prize, activity: Activity) -> None:
    _feel(hero, "fear", 1)
    _feel(hero, "shyness", 1)
    world.say(
        f"{hero.id} whispered, 'What if everyone stares at my udder?'"
    )
    world.say(
        f"{faculty.label} noticed the worry and said the thought was bigger than the problem."
    )


def shift_perspective(world: World, hero: Entity, faculty: Entity) -> None:
    _feel(hero, "courage", 1)
    hero.memes["fear"] = 0.0
    world.story_view = "brave"
    world.say(
        f"{faculty.label} asked {hero.id} to look at the room from a kinder perspective."
    )
    world.say(
        f"'From this perspective,' {faculty.label} said, 'your udder is not a flaw. It is just part of being a cow.'"
    )


def perform(world: World, hero: Entity, activity: Activity) -> None:
    _boost(hero, "voice", 1)
    _feel(hero, "joy", 1)
    world.say(
        f"{hero.id} took a breath, stood tall, and began to {activity.verb}."
    )
    world.say(
        f"{hero.id} said, '{activity.keyword.title()} and play, let the day be bright; "
        f"milk and bells and sunny light!'"
    )


def applause(world: World, faculty: Entity, hero: Entity) -> None:
    _feel(hero, "love", 1)
    world.say(
        f"The class clapped, and the faculty smiled."
    )
    world.say(
        f"{faculty.label} said the rhyme was lovely, and {hero.id} had used the kinder perspective well."
    )


def ending(world: World, hero: Entity) -> None:
    world.say(
        f"After that, {hero.id} did not hide. {hero.pronoun().capitalize()} stood on the rug with a calm heart, "
        f"and the udder was just part of a happy cow at school."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Molly", hero_type: str = "cow",
         faculty_name: str = "Mrs. Finch", faculty_type: str = "teacher") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "gentle"]))
    faculty = world.add(Entity(id=faculty_name, kind="character", type=faculty_type, label=faculty_name))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))

    introduce(world, hero)
    faculty_note(world, faculty)
    love_rhyme(world, hero, activity)
    buy_prize(world, faculty, hero, prize)
    wear_prize(world, hero, prize)
    world.para()
    arrive(world, hero, faculty, activity)
    worry(world, hero, faculty, prize, activity)
    shift_perspective(world, hero, faculty)
    world.para()
    perform(world, hero, activity)
    applause(world, faculty, hero)
    ending(world, hero)

    world.facts.update(hero=hero, faculty=faculty, prize=prize, activity=activity, setting=setting)
    return world


SETTINGS = {
    "school_barn": Setting(place="the school barn", affords={"rhyme"}),
    "reading_rug": Setting(place="the reading rug", affords={"rhyme"}),
}

ACTIVITIES = {
    "rhyme": Activity(
        id="rhyme",
        verb="sing a rhyme",
        gerund="singing rhymes",
        rush="dash to the stage",
        mess="tremble",
        soil="look shy",
        venue="stage",
        keyword="rhyme",
        tags={"rhyme", "school", "perspective"},
    ),
}

PRIZES = {
    "badge": Prize(label="badge", phrase="a shiny star badge", type="badge", worn_region="chest"),
    "scarf": Prize(label="scarf", phrase="a soft blue scarf", type="scarf", worn_region="neck"),
}

GIRL_NAMES = ["Molly", "Daisy", "Luna", "Nell", "Bessie"]
BOY_NAMES = ["Otis", "Milo", "Henry", "Clover", "Pip"]
TRAITS = ["brave", "gentle", "curious", "quiet", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    faculty: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for a in setting.affords:
            for p in PRIZES:
                combos.append((s, a, p))
    return combos


KNOWLEDGE = {
    "rhyme": [("What is a rhyme?", "A rhyme is a pair of words that sound alike at the end, like cat and hat.")],
    "perspective": [("What does perspective mean?", "Perspective means the way someone sees or thinks about a thing.")],
    "cow": [("What is a cow?", "A cow is a farm animal that can make milk.")],
    "udder": [("What is an udder?", "An udder is the part of a cow where milk comes from.")],
    "school": [("What is a school?", "A school is a place where children and teachers learn together.")],
    "faculty": [("Who is faculty at a school?", "Faculty are the teachers and staff who help children learn and stay safe.")],
}

KNOWLEDGE_ORDER = ["school", "faculty", "rhyme", "perspective", "cow", "udder"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, faculty, act = f["hero"], f["faculty"], f["activity"]
    return [
        f'Write a short animal story about a little {hero.type} named {hero.id} who wants to {act.verb} at school.',
        f'Tell a gentle story where {faculty.label}, as part of the faculty, helps {hero.id} find a kinder perspective.',
        f'Write a child-friendly story that includes the words "faculty", "udder", and "perspective" and ends with a happy rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, faculty, act = f["hero"], f["faculty"], f["activity"]
    setting = f["setting"].place
    return [
        QAItem(
            question=f"Who wanted to sing a rhyme at {setting}?",
            answer=f"{hero.id}, a little {hero.type}, wanted to {act.verb} at {setting}.",
        ),
        QAItem(
            question=f"Who was part of the faculty and helped {hero.id}?",
            answer=f"{faculty.label} was part of the faculty and helped {hero.id} feel calm.",
        ),
        QAItem(
            question=f"What did {hero.id} need to change before going on the stage?",
            answer=f"{hero.id} needed a kinder perspective about {hero.pronoun('possessive')} udder, so {hero.pronoun()} could perform without hiding.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} stood on the rug, sang the rhyme, and felt brave while the class clapped.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["activity"].tags)
    tags.update({"faculty", "perspective", "rhyme", "cow", "udder", "school"})
    for tag in KNOWLEDGE_ORDER:
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  view: {world.story_view}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,A,P) :- setting(S), affords(S,A), prize(P).
story_theme(A) :- valid_story(_,A,_), activity(A).
needs_perspective(A) :- story_theme(A).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about faculty, udder, perspective, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--faculty")
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    faculty = args.faculty or rng.choice(["Mrs. Finch", "Mr. Bramble", "Ms. Clover"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, faculty=faculty, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, "cow", params.faculty, "teacher")
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
    StoryParams(setting="school_barn", activity="rhyme", prize="badge", name="Molly", gender="girl", faculty="Mrs. Finch", trait="gentle"),
    StoryParams(setting="reading_rug", activity="rhyme", prize="scarf", name="Otis", gender="boy", faculty="Mr. Bramble", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible story combos:\n")
        for triple in triples:
            print(" ", triple)
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
            header = f"### {p.name}: {p.activity} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
