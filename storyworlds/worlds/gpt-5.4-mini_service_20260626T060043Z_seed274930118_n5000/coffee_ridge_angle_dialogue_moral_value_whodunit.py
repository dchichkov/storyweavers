#!/usr/bin/env python3
"""
storyworlds/worlds/coffee_ridge_angle_dialogue_moral_value_whodunit.py
======================================================================

A small whodunit storyworld built from the seed words coffee, ridge, and angle.

Premise:
- A child-detective visits a ridge cafe where a cup of coffee goes missing.
- The mystery is solved by noticing the angle of a spill trail and by asking
  careful questions instead of blaming too fast.
- The moral value is honesty: the real answer comes from truthfully sharing
  what each person saw.

The world is intentionally small and constraint-checked:
- A coffee item can spill on a ridge path.
- A clue angle matters because the trail points toward where the cup went.
- Dialogue moves the story.
- The ending proves the clue changed the investigation and the characters'
  feelings.

This script follows the Storyworld contract:
- self-contained stdlib script
- eager import of storyworlds.results
- lazy import of storyworlds.asp in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and exercises generated stories
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
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
    place: str = "the ridge cafe"
    outside: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    verb: str
    gerund: str
    suspect_verb: str
    clue_word: str
    mess: str
    angle_use: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    setting: str
    mystery: str
    prize: str
    hero_name: str
    hero_gender: str
    partner_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "ridge": Setting(place="the ridge cafe", outside=True, affords={"coffee"}),
    "porch": Setting(place="the porch by the ridge", outside=True, affords={"coffee"}),
    "trail": Setting(place="the trail overlook", outside=True, affords={"coffee"}),
}

MYSTERIES = {
    "missing_cup": Mystery(
        id="missing_cup",
        title="the missing coffee cup",
        verb="find the missing cup",
        gerund="looking for the missing cup",
        suspect_verb="hide the cup",
        clue_word="angle",
        mess="spill",
        angle_use="the spill angled toward the bench",
        location="by the stone bench",
        tags={"coffee", "angle", "ridge", "dialogue", "moral_value", "whodunit"},
    ),
    "stolen_sugar": Mystery(
        id="stolen_sugar",
        title="the stolen sugar jar",
        verb="find the sugar jar",
        gerund="searching for the sugar jar",
        suspect_verb="take the sugar",
        clue_word="angle",
        mess="crumbs",
        angle_use="the crumbs angled toward the shelf",
        location="near the back shelf",
        tags={"coffee", "angle", "ridge", "dialogue", "moral_value", "whodunit"},
    ),
}

PRIZES = {
    "cup": Prize(label="cup", phrase="a warm coffee cup", type="cup", location="table"),
    "notebook": Prize(label="notebook", phrase="a small notebook", type="notebook", location="pocket"),
}

HELPERS = [
    Helper(id="lamp", label="a tiny lamp", prep="turn on the tiny lamp", tail="let the lamp shine on the clue", protects={"dark"}),
    Helper(id="tray", label="a steady tray", prep="use a steady tray", tail="carry the coffee more carefully", protects={"spill"}),
]

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Elsa", "Lila"]
BOY_NAMES = ["Theo", "Milo", "Owen", "Eli", "Finn"]
TRAITS = ["curious", "careful", "brave", "quiet", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for m_id, mystery in MYSTERIES.items():
            for p_id, prize in PRIZES.items():
                if prize.location == "table" and "coffee" in mystery.tags and setting.outside:
                    combos.append((s_id, m_id, p_id))
    return combos


def reasonableness_gate(setting: Setting, mystery: Mystery, prize: Prize) -> bool:
    return (prize.location == "table" and "coffee" in mystery.tags and setting.outside)


def explain_rejection(setting: Setting, mystery: Mystery, prize: Prize) -> str:
    return (
        f"(No story: {mystery.title} needs a coffee-side clue on an outdoor ridge scene, "
        f"and {prize.label} must belong on the table. This combination does not give the story "
        f"a believable clue or an honest mystery.)"
    )


def clue_selector(mystery: Mystery, prize: Prize) -> Optional[Helper]:
    for helper in HELPERS:
        if mystery.id == "missing_cup" and "spill" in helper.protects:
            return helper
        if mystery.id == "stolen_sugar" and "spill" not in helper.protects:
            return helper
    return None


def predict_truth(world: World, hero: Entity, mystery: Mystery, prize: Entity) -> dict:
    sim = world.copy()
    _advance_mystery(sim, sim.get(hero.id), mystery, prize, narrate=False)
    return {
        "solved": sim.facts.get("solved", False),
        "truth_told": sim.facts.get("truth_told", False),
    }


def _advance_mystery(world: World, hero: Entity, mystery: Mystery, prize: Entity, narrate: bool = True) -> None:
    if mystery.id == "missing_cup":
        prize.meters["missing"] = 1.0
        prize.location = "nowhere"
        world.facts["solved"] = True
        world.facts["truth_told"] = True
        if narrate:
            world.say("The cup was missing, but the trail of coffee pointed in one careful direction.")
    else:
        world.facts["solved"] = True
        world.facts["truth_told"] = True
        if narrate:
            world.say("The clues were small, but every honest answer made the shape of the mystery clearer.")


def tell_story(world: World, hero: Entity, partner: Entity, prize: Entity, mystery: Mystery, helper: Optional[Helper]) -> None:
    setting = world.setting
    world.say(
        f"{hero.id} was a {hero.traits[0]} child who loved quiet riddles, and {partner.id} "
        f"liked to solve them with {hero.pronoun('possessive')} {mystery.clue_word}."
    )
    world.say(
        f"At {setting.place}, the air smelled like coffee, and everyone said the ridge looked "
        f"so steep that even the shadows leaned at an angle."
    )
    world.para()
    world.say(
        f"Then {hero.id} noticed that {prize.phrase} was gone from the table."
    )
    world.say(
        f'"Did you take it?" {hero.id} asked. "No," said {partner.id}, "but I saw something odd near {mystery.location}."'
    )
    world.say(
        f"{hero.id} knelt down and studied the {mystery.clue_word}. {mystery.angle_use.capitalize()}."
    )
    if helper:
        world.say(
            f'"Maybe we should {helper.prep}," said {partner.id}. "A careful look is better than a fast guess."'
        )
    world.para()
    world.say(
        f"{hero.id} followed the clue instead of blaming the first face that looked worried."
    )
    if mystery.id == "missing_cup":
        world.say(
            f"Behind the bench, the coffee cup had rolled into a shallow crack, where the wind had hidden it from sight."
        )
    else:
        world.say(
            f"The sugar jar had slipped behind the shelf after someone bumped the tray, and the little crumbs told the truth."
        )
    world.say(
        f'"I should have said what I saw sooner," admitted {partner.id}. "Truth helps more than guessing."'
    )
    world.say(
        f"{hero.id} smiled. The mystery was solved, the coffee stayed warm, and the ridge felt calmer because nobody had to hide the truth anymore."
    )

    world.facts.update(
        hero=hero,
        partner=partner,
        prize=prize,
        mystery=mystery,
        helper=helper,
        solved=True,
        truth_told=True,
        setting=setting,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit for a child where {f['hero'].id} solves {f['mystery'].title} at {f['setting'].place}.",
        f"Tell a dialogue-heavy mystery story that uses the words coffee, ridge, and angle, and ends with an honest confession.",
        f"Write a gentle detective story in which careful observation matters more than blaming someone too quickly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    mystery: Mystery = f["mystery"]
    prize: Entity = f["prize"]
    helper: Optional[Helper] = f["helper"]

    qa = [
        QAItem(
            question=f"What mystery did {hero.id} try to solve at {f['setting'].place}?",
            answer=f"{hero.id} tried to solve {mystery.title} at {f['setting'].place}. The story began when the coffee-side clue went missing.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"The clue was the {mystery.clue_word}. The tilted trail showed where the missing thing had gone.",
        ),
        QAItem(
            question=f"Who talked with {hero.id} during the investigation?",
            answer=f"{partner.id} talked with {hero.id}, and their dialogue helped them think carefully instead of guessing too fast.",
        ),
        QAItem(
            question=f"What did the final clue prove about {prize.label}?",
            answer=f"It proved that {prize.phrase} had not been stolen by a mean trick. The clue led to the real hiding place, so the truth came out.",
        ),
    ]
    if helper:
        qa.append(
            QAItem(
                question=f"How did {helper.label} help during the mystery?",
                answer=f"{helper.label} helped because it encouraged a careful search. The characters used it to look closely instead of rushing.",
            )
        )
    qa.append(
        QAItem(
            question="What moral did the story teach?",
            answer="The story taught that honesty and careful looking are better than quick blame. Telling the truth helps solve problems.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is coffee?",
            answer="Coffee is a dark, warm drink people often sip when they want something cozy or energizing.",
        ),
        QAItem(
            question="What is a ridge?",
            answer="A ridge is a long raised line of land, often higher than the ground around it.",
        ),
        QAItem(
            question="What does angle mean?",
            answer="An angle is the shape made when two lines or surfaces meet, and it can help show direction or tilt.",
        ),
        QAItem(
            question="Why is it important to tell the truth?",
            answer="Telling the truth helps people understand what really happened, which makes it easier to fix problems and trust each other.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- place(S).
compatible(S,M,P) :- outdoor(S), coffee_mystery(M), table_prize(P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.outside:
            lines.append(asp.fact("outdoor", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("coffee_mystery", mid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("table_prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set, py_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with coffee, ridge, and angle.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    partner_gender = args.partner_gender or ("boy" if gender == "girl" else "girl")
    return StoryParams(setting=setting, mystery=mystery, prize=prize, hero_name=name, hero_gender=gender, partner_gender=partner_gender)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    prize = PRIZES[params.prize]
    if not reasonableness_gate(setting, mystery, prize):
        raise StoryError(explain_rejection(setting, mystery, prize))

    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, traits=[rng_trait(params.seed)]))
    partner_name = "Rae" if params.hero_name != "Rae" else "June"
    partner = world.add(Entity(id=partner_name, kind="character", type=params.partner_gender, traits=["honest"]))
    prize_ent = world.add(Entity(id="prize", type=prize.type, label=prize.label, phrase=prize.phrase, location=prize.location))
    helper = clue_selector(mystery, prize)
    tell_story(world, hero, partner, prize_ent, mystery, helper)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def rng_trait(seed: Optional[int]) -> str:
    rng = random.Random(seed)
    return rng.choice(TRAITS)


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
    StoryParams(setting="ridge", mystery="missing_cup", prize="cup", hero_name="Mina", hero_gender="girl", partner_gender="boy"),
    StoryParams(setting="porch", mystery="stolen_sugar", prize="notebook", hero_name="Theo", hero_gender="boy", partner_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.hero_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
