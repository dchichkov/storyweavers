#!/usr/bin/env python3
"""
storyworlds/worlds/allure_nerve_obstinate_repetition_rhyming_story.py
======================================================================

A small, standalone storyworld about a tempting shine, a brave little nerve,
and an obstinate rhyme that helps a child keep on track.

Premise:
- A child must bring a fragile or tasty prize through a place full of allure.
- The allure is vivid and persuasive: sweet smells, sparkle, music, or glitter.
- The child's parent or helper warns them that straying will ruin the prize.
- The child repeats a little rhyme to build nerve.
- Obstinate repetition can become a strength when it is aimed at the right task.

The story engine models:
- physical meters: sparkle, mess, damage, distance, safety
- emotional memes: allure, nerve, obstinate, worry, pride, relief

The prose is intentionally rhyming and repetitive, but not frozen: it is driven
by simulated state changes and a single causal turn from temptation to resolve.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
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
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    lure: str
    rhyme: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Safeguard:
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
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


@dataclass
class StoryParams:
    place: str
    temptation: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow", indoors=False, affords={"gleam", "bell"}),
    "market": Setting(place="the market", indoors=False, affords={"gleam", "treat"}),
    "hall": Setting(place="the little hall", indoors=True, affords={"song", "gleam"}),
}

TEMPTATIONS = {
    "gleam": Temptation(
        id="gleam",
        lure="a glittery game",
        rhyme="Gleam and beam, I do not stray from my seam",
        rush="run after the sparkle",
        mess="scattered",
        soil="scuffed and scattered",
        zone={"feet"},
        keyword="gleam",
        tags={"sparkle"},
    ),
    "bell": Temptation(
        id="bell",
        lure="a jingling bell",
        rhyme="Ring and sing, I carry the thing",
        rush="dash toward the ringing",
        mess="jostled",
        soil="jostled and dusty",
        zone={"hands"},
        keyword="bell",
        tags={"sound"},
    ),
    "treat": Temptation(
        id="treat",
        lure="sweet taffy smells",
        rhyme="Treat and keep, I walk and неep".replace("неep", "sleep"),
        rush="skip toward the sweets",
        mess="sticky",
        soil="sticky and smudged",
        zone={"hands", "mouth"},
        keyword="treat",
        tags={"sweet"},
    ),
    "song": Temptation(
        id="song",
        lure="a bright chorus",
        rhyme="Sing and cling, I finish the thing",
        rush="swerve toward the music",
        mess="distracted",
        soil="distracted and delayed",
        zone={"head"},
        keyword="song",
        tags={"music"},
    ),
}

PRIZES = {
    "basket": Prize(id="basket", label="basket", phrase="a small woven basket", region="hands"),
    "cake": Prize(id="cake", label="cake", phrase="a frosted cake box", region="hands"),
    "lantern": Prize(id="lantern", label="lantern", phrase="a paper lantern", region="hands"),
    "cape": Prize(id="cape", label="cape", phrase="a bright cape", region="torso"),
}

SAFEGUARDS = [
    Safeguard(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"sticky", "jostled"},
        prep="put on soft gloves first",
        tail="put on the soft gloves and walked on",
        plural=True,
    ),
    Safeguard(
        id="wrap",
        label="a wrap",
        covers={"hands", "torso"},
        guards={"scuffed", "distracted"},
        prep="wrap it up gently first",
        tail="wrapped it up and went along",
    ),
]


GIRL_NAMES = ["Mina", "Lila", "Pia", "Nora", "Tia", "Zia", "Eva"]
BOY_NAMES = ["Owen", "Beck", "Finn", "Cole", "Nico", "Theo", "Jude"]
TRAITS = ["brave", "curious", "obstinate", "gentle", "bouncy"]


def prize_at_risk(temptation: Temptation, prize: Prize) -> bool:
    return prize.region in temptation.zone


def select_safeguard(temptation: Temptation, prize: Prize) -> Optional[Safeguard]:
    for s in SAFEGUARDS:
        if temptation.mess in s.guards and prize.region in s.covers:
            return s
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for temp_id in setting.affords:
            t = TEMPTATIONS[temp_id]
            for prize_id, pr in PRIZES.items():
                if prize_at_risk(t, pr) and select_safeguard(t, pr):
                    out.append((place, temp_id, prize_id))
    return out


def build_world(setting: Setting, temptation: Temptation, prize_cfg: Prize,
                name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    hero.type = gender
    hero.kind = "character"
    hero.memes.update({"allure": 0.0, "nerve": 0.0, "obstinate": 0.0, "worry": 0.0, "pride": 0.0, "relief": 0.0})
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={"damage": 0.0},
    ))
    hero.memes["obstinate"] += 1.0 if trait == "obstinate" else 0.5
    world.facts.update(hero=hero, parent=parent, prize=prize, temptation=temptation, trait=trait)
    return world


def maybe_rhyme(world: World, hero: Entity, temptation: Temptation) -> None:
    hero.memes["obstinate"] += 1
    hero.memes["nerve"] += 1
    world.say(f'{hero.id} took a breath and said, "{temptation.rhyme}."')
    world.say(f"Again and again, the little line rang true; again and again, the little line grew new.")
    world.say(f"{hero.id} was obstinate, yes, but the obstinate tune gave {hero.pronoun('object')} nerve.")


def predict_damage(world: World, temptation: Temptation, prize: Entity) -> bool:
    return prize_at_risk(temptation, PRIZES[prize.type])


def resolve(world: World, temptation: Temptation, prize: Entity) -> Optional[Safeguard]:
    safeguard = select_safeguard(temptation, PRIZES[prize.type])
    if safeguard is None:
        return None
    return safeguard


def tell(setting: Setting, temptation: Temptation, prize_cfg: Prize,
         name: str = "Mina", gender: str = "girl",
         parent_type: str = "mother", trait: str = "brave") -> World:
    world = build_world(setting, temptation, prize_cfg, name, gender, parent_type, trait)
    hero = world.get(name)
    parent = world.get("Parent")
    prize = world.get("Prize")
    world.say(f"{hero.id} was a {trait} little {gender} who liked to sing and stroll.")
    world.say(f"But near {setting.place}, there was {temptation.lure}, all glitter and sparkle and roll.")
    world.say(f"{hero.id} loved the shine, the jingle, the sweet little call, but {hero.pronoun('possessive')} {parent.label or 'parent'} held the prize.")
    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label_word if hasattr(parent, 'label_word') else 'parent'} went to {setting.place}.")
    world.say(f"{hero.id} wanted to follow the lure, to follow the lure, to follow it near.")
    hero.memes["allure"] += 1
    hero.memes["worry"] += 1
    world.say(f"But the {prize.label} had to stay safe and sound, so the parent said, 'Keep your mind right here.'")
    maybe_rhyme(world, hero, temptation)
    world.say(f"{hero.id} started to drift, then paused in the thick of the strife.")
    if predict_damage(world, temptation, prize):
        world.say(f"'{temptation.rush.capitalize()},' {hero.id} thought, 'but that would spoil the prize and dull the bright life.'")
    world.say(f"{hero.id} clenched {hero.pronoun('possessive')} hands and held the task tight-tight-tight.")
    safeguard = resolve(world, temptation, prize)
    world.para()
    if safeguard is not None:
        world.say(f"{parent.label if parent.label else 'the parent'} smiled and said, 'Try {safeguard.label} first; that will make it right.'")
        world.say(f"They {safeguard.tail}, and the trip went smooth in the light.")
        hero.memes["nerve"] += 1
        hero.memes["relief"] += 1
        hero.memes["pride"] += 1
        prize.meters["damage"] = 0.0
        world.say(f"In the end, {hero.id} was still singing the same little line, but now it sounded bright: {temptation.rhyme}.")
        world.say(f"{hero.id} brought home the {prize.label} safe and clean, and the day felt snug and right.")
    else:
        world.say(f"No safe fix fit the prize, so they turned away from the shine.")
        hero.memes["relief"] += 1
        world.say(f"{hero.id} repeated the rhyme once more, and the brave little heart stayed fine.")
    world.facts.update(safeguard=safeguard, resolved=safeguard is not None)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    temp = f["temptation"]
    return [
        f'Write a short rhyming story for a young child about {hero.id}, a tempting {temp.keyword}, and a fragile {prize.label}.',
        f"Tell a little story where a child with obstinate repetition finds nerve instead of giving in to {temp.lure}.",
        f'Write a child-friendly rhyme about keeping a {prize.label} safe while resisting {temp.keyword}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    temp = f["temptation"]
    safeguard = f.get("safeguard")
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to keep safe?",
            answer=f"{hero.id} was trying to keep {hero.pronoun('possessive')} {prize.label} safe while walking through {world.setting.place}.",
        ),
        QAItem(
            question=f"What kept trying to lure {hero.id} away?",
            answer=f"The lure was {temp.lure}, and it kept tugging at {hero.id}'s attention.",
        ),
        QAItem(
            question=f"What did {hero.id} repeat to get more nerve?",
            answer=f"{hero.id} repeated, '{temp.rhyme}.' The rhyme helped {hero.id} stay steady.",
        ),
        QAItem(
            question=f"Why did the parent worry?",
            answer=f"The parent worried because if {hero.id} chased the lure, the {prize.label} could get {temp.soil}.",
        ),
    ]
    if safeguard is not None:
        qa.append(QAItem(
            question=f"What helped {hero.id} finish the trip without trouble?",
            answer=f"{safeguard.label} helped {hero.id} finish the trip safely, because it fit the task and covered the right part of the prize.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and relieved, because the prize stayed safe and the rhyme worked like a brave little drumbeat.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    temp = f["temptation"]
    out = [
        QAItem(
            question="What does allure mean?",
            answer="Allure means a strong pull or charm that makes something seem very tempting.",
        ),
        QAItem(
            question="What is nerve?",
            answer="Nerve means courage or boldness, especially when someone feels worried but tries anyway.",
        ),
        QAItem(
            question="What does obstinate mean?",
            answer="Obstinate means stubborn in a way that does not change easily, even when someone is told to stop.",
        ),
        QAItem(
            question="Why can repetition help?",
            answer="Repetition can help because saying the same words again and again can make a plan feel steadier and easier to remember.",
        ),
    ]
    if "sparkle" in temp.tags:
        out.append(QAItem(
            question="Why do shiny things catch the eye?",
            answer="Shiny things catch the eye because light bounces off them and makes them look bright and lively.",
        ))
    if "sweet" in temp.tags:
        out.append(QAItem(
            question="Why do sweet smells feel tempting?",
            answer="Sweet smells can feel tempting because they make people imagine a tasty treat nearby.",
        ))
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
        lines.append(f"  {e.id}: ({e.kind}/{e.type}) " + " ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", temptation="gleam", prize="basket", name="Mina", gender="girl", parent="mother", trait="obstinate"),
    StoryParams(place="market", temptation="treat", prize="cake", name="Owen", gender="boy", parent="father", trait="brave"),
    StoryParams(place="hall", temptation="song", prize="cape", name="Pia", gender="girl", parent="mother", trait="curious"),
]


def explain_rejection(temptation: Temptation, prize: Prize) -> str:
    return f"(No story: {temptation.lure} does not threaten a {prize.label} worn on the {prize.region}, so the warning would not be honest.)"


def valid_gender(prize_id: str, gender: str) -> bool:
    return gender in PRIZES[prize_id].genders


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld of allure, nerve, and obstinate repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
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
    if args.gender and args.prize and not valid_gender(args.prize, args.gender):
        raise StoryError("The chosen prize does not fit that gender in this world.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.temptation is None or c[1] == args.temptation)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid story matches those choices.)")
    place, temp_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, temptation=temp_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TEMPTATIONS[params.temptation], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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


ASP_RULES = r"""
place(P) :- setting(P).
temptation(T) :- tempt(T).
prize(P) :- prize_item(P).

at_risk(T, P) :- splashes(T, R), worn_on(P, R).
fix(T, P) :- at_risk(T, P), guards(G, M), covers(G, R), mess_of(T, M), worn_on(P, R).
valid(Place, T, P) :- affords(Place, T), at_risk(T, P), fix(T, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("tempt", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        for r in sorted(t.zone):
            lines.append(asp.fact("splashes", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize_item", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in SAFEGUARDS:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, temp, prize in triples:
            print(f"  {place:8} {temp:10} {prize}")
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
            header = f"### {p.name}: {p.temptation} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
