#!/usr/bin/env python3
"""
storyworlds/worlds/lure_recess_suspense_bedtime_story.py
=========================================================

A small bedtime-story world about a child at recess, a tempting lure, and a
gentle suspenseful turn that resolves safely before sleep.

The seed tale behind this world:
---
At recess, Mina found a shiny silver lure tied to a string near the school
garden. It twinkled like a tiny moon and seemed to whisper, "Come closer."
Mina wanted to follow it, but the recess bell had already rung twice and the
teacher had said everyone must come inside before bedtime.

Mina stepped toward the lure anyway. The string led behind a low hedge where
the grass was dark and the air felt quiet and mysterious. Mina's chest felt
tight. Then she saw that the lure was not magic at all: it was a lost charm
hanging from the class kite. Mina brought it back, and the teacher smiled and
said Mina could help tie it to the kite for tomorrow. At bedtime, Mina hugged
the blanket and felt brave.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
    meter: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
    place: str = "the schoolyard"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    label: str
    phrase: str
    glints: str
    leads_to: str
    risk: str
    calm_fix: str
    keyword: str = "lure"
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
class Comfort:
    id: str
    label: str
    covers: set[str]
    soothes: set[str]
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
        self.zone: set[str] = set()
        self.phase: str = "setup"

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
        clone.zone = set(self.zone)
        clone.phase = self.phase
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        if actor.meters["risk"] < THRESHOLD:
            continue
        sig = ("suspense", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["suspense"] += 1
        out.append(f"The quiet felt bigger now.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["suspense"] < THRESHOLD:
            continue
        if actor.meters["safe"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["suspense"] = 0.0
        actor.memes["relief"] += 1
        out.append(f"The worry began to soften.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("suspense", "social", _r_suspense),
    Rule("calm", "social", _r_calm),
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


def lure_at_risk(lure: Lure) -> bool:
    return True


def select_comfort(lure: Lure, prize: Prize) -> Optional[Comfort]:
    for item in COMFORTS:
        if lure.risk in item.soothes and prize.region in item.covers:
            return item
    return None


def predict(world: World, hero: Entity, lure: Lure, prize_id: str) -> dict:
    sim = world.copy()
    _approach_lure(sim, sim.get(hero.id), lure, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "lost": bool(prize.memes["lost"] >= THRESHOLD),
        "safe": sum(e.meters["safe"] for e in sim.characters()),
    }


def _approach_lure(world: World, hero: Entity, lure: Lure, narrate: bool = True) -> None:
    hero.meters["risk"] += 1
    hero.memes["curiosity"] += 1
    world.zone = {"hedge", "path"}
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{hero.id} leaned closer to the {lure.label}, and the path ahead felt "
            f"very quiet indeed."
        )


def _recover_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.meters["safe"] += 1
    prize.memes["found"] += 1


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who liked to notice tiny things "
        f"at the edge of the day."
    )


def loves_recess(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved recess at {setting.place} because "
        f"there were leaves to chase, chalk lines to hop over, and secret corners to imagine."
    )


def finds_lure(world: World, hero: Entity, lure: Lure) -> None:
    world.say(
        f"Near a low hedge, {hero.id} spotted {lure.phrase}. It glinted {lure.glints} "
        f"and seemed to {lure.leads_to}."
    )


def warning(world: World, adult: Entity, hero: Entity, lure: Lure, prize: Prize) -> bool:
    pred = predict(world, hero, lure, prize.id)
    if not pred["lost"]:
        return False
    hero.meters["risk"] += 1
    world.facts["predicted_risk"] = lure.risk
    world.say(
        f'"Be careful," {adult.pronoun("subject")} said. "That {lure.label} could lead '
        f"you somewhere hidden, and then your {prize.label} might be left behind.""
    )
    return True


def suspense_step(world: World, hero: Entity, lure: Lure) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} took one small step, then another. The string trembled, and the air "
        f"felt like it was holding its breath."
    )
    world.say(
        f"Then {hero.id} wondered if the {lure.label} was a clue, a lost treasure, or just "
        f"something waiting to be carried home."
    )


def reveal(world: World, hero: Entity, lure: Lure, prize: Entity) -> None:
    _recover_prize(world, hero, prize)
    world.say(
        f"At last, the mystery was only a lost charm from the class kite. {hero.id} "
        f"picked it up carefully and brought it back."
    )


def compromise(world: World, adult: Entity, hero: Entity, lure: Lure, prize: Entity) -> Optional[Comfort]:
    comfort = select_comfort(lure, prize)
    if comfort is None:
        return None
    world.add(Entity(
        id=comfort.id,
        type="comfort",
        label=comfort.label,
        owner=hero.id,
        caretaker=adult.id,
        plural=comfort.plural,
    ))
    world.say(
        f'"How about we use {comfort.label} first?" {adult.pronoun("subject")} asked. '
        f"That way, {hero.id} could be brave without losing the way back."
    )
    return comfort


def resolve(world: World, hero: Entity, adult: Entity, comfort: Comfort, lure: Lure, prize: Entity) -> None:
    hero.meters["safe"] += 1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["suspense"] = 0.0
    world.say(
        f"{hero.id} nodded and held the {comfort.label}. Together they followed the clue, "
        f"found the {prize.label}, and returned before the last bell."
    )
    world.say(
        f"By bedtime, the {lure.label} was no longer scary at all. It had become a small "
        f"good thing, tucked safely where it belonged, while {hero.id} snuggled warm and calm."
    )


def tell(setting: Setting, lure: Lure, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, adult_type: str = "teacher") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "gentle"]),
    ))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, label="the teacher"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=adult.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    intro(world, hero)
    loves_recess(world, hero, setting)
    world.say(
        f"That afternoon, {hero.id} wore {hero.pronoun('possessive')} {prize.label} and "
        f"looked forward to the end of recess."
    )

    world.para()
    finds_lure(world, hero, lure)
    warning(world, adult, hero, lure, prize)
    suspense_step(world, hero, lure)

    world.para()
    comfort = compromise(world, adult, hero, lure, prize)
    if comfort:
        reveal(world, hero, lure, prize)
        resolve(world, hero, adult, comfort, lure, prize)

    world.facts.update(
        hero=hero,
        adult=adult,
        prize=prize,
        lure=lure,
        setting=setting,
        comfort=comfort,
        resolved=comfort is not None,
    )
    return world


SETTINGS = {
    "schoolyard": Setting(place="the schoolyard", indoor=False, affords={"recess"}),
    "garden": Setting(place="the garden behind the school", indoor=False, affords={"recess"}),
    "playground": Setting(place="the playground", indoor=False, affords={"recess"}),
}

LURES = {
    "silver_charm": Lure(
        id="silver_charm",
        label="silver charm",
        phrase="a shiny silver charm tied to a string",
        glints="like a tiny moon",
        leads_to="call softly from behind the hedge",
        risk="lost",
        calm_fix="follow carefully",
        tags={"lure", "shiny"},
    ),
    "paper_star": Lure(
        id="paper_star",
        label="paper star",
        phrase="a paper star dangling from a branch",
        glints="in the late light",
        leads_to="point toward the quiet path",
        risk="lost",
        calm_fix="take it home",
        tags={"lure", "paper"},
    ),
    "glass_bead": Lure(
        id="glass_bead",
        label="glass bead",
        phrase="a glass bead on a blue ribbon",
        glints="with a sleepy sparkle",
        leads_to="flicker near the fence",
        risk="lost",
        calm_fix="bring it back",
        tags={"lure", "sparkle"},
    ),
}

PRIZES = {
    "blanket": Prize(label="blanket", phrase="a soft bedtime blanket", type="blanket", region="torso"),
    "sweater": Prize(label="sweater", phrase="a warm striped sweater", type="sweater", region="torso"),
    "cap": Prize(label="cap", phrase="a little red cap", type="cap", region="head"),
}

COMFORTS = [
    Comfort(
        id="flashlight",
        label="a small flashlight",
        covers={"path", "hedge"},
        soothes={"lost"},
        prep="carry a small flashlight",
        tail="followed the light home",
    ),
    Comfort(
        id="hand",
        label="the teacher's hand",
        covers={"path"},
        soothes={"lost"},
        prep="hold the teacher's hand",
        tail="walked back together",
    ),
]

HERO_NAMES = ["Mina", "Lia", "Noah", "Sofi", "Eli", "Tess", "Ari", "June"]
TRAITS = ["curious", "gentle", "quiet", "brave", "careful", "dreamy"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for lure_id in setting.affords:
            for prize_id in PRIZES:
                if lure_at_risk(LURES["silver_charm"]):
                    combos.append((place, lure_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    lure: str
    prize: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "lure": [
        ("What is a lure?",
         "A lure is something that catches your attention and makes you want to follow it, like a shiny object or a tempting hint."),
    ],
    "recess": [
        ("What is recess?",
         "Recess is a break at school when children can move around, play, and rest their minds for a little while."),
    ],
    "suspense": [
        ("What is suspense in a story?",
         "Suspense is the feeling of wondering what will happen next, especially when something feels a little mysterious."),
    ],
    "bedtime": [
        ("Why do children need bedtime?",
         "Bedtime helps a child’s body and mind rest so they can feel ready for a new day."),
    ],
    "lost": [
        ("What does it mean if something is lost?",
         "If something is lost, it is not where it was supposed to be, so someone may have to look for it."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, adult, lure, prize = f["hero"], f["adult"], f["lure"], f["prize"]
    return [
        f'Write a bedtime story for a young child that includes the word "lure" and happens during recess.',
        f"Tell a suspenseful but gentle story where {hero.id} at {f['setting'].place} notices {lure.phrase} while wearing {prize.phrase}.",
        f"Write a short bedtime story in which a child follows a tempting lure at recess, feels suspense, and returns safely before sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, adult, prize, lure = f["hero"], f["adult"], f["prize"], f["lure"]
    qa = [
        QAItem(
            question=f"Where did {hero.id} notice the {lure.label}?",
            answer=f"{hero.id} noticed it during recess at {f['setting'].place}.",
        ),
        QAItem(
            question=f"Why did the teacher worry about the {lure.label}?",
            answer=f"The teacher worried because the {lure.label} could lead {hero.id} somewhere hidden and leave the {prize.label} behind.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"It felt suspenseful because {hero.id} stepped toward the {lure.label} and the path ahead seemed quiet and mysterious.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end for {hero.id}?",
                answer=f"{hero.id} found the lost charm, brought it back, and ended the day safe and calm at bedtime.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["lure"].tags)
    out: list[QAItem] = []
    for tag in ["lure", "recess", "suspense", "bedtime", "lost"]:
        if tag in tags or tag in KNOWLEDGE:
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="schoolyard", lure="silver_charm", prize="blanket", name="Mina", gender="girl", adult="teacher", trait="curious"),
    StoryParams(place="garden", lure="paper_star", prize="sweater", name="Noah", gender="boy", adult="teacher", trait="gentle"),
    StoryParams(place="playground", lure="glass_bead", prize="cap", name="Tess", gender="girl", adult="teacher", trait="careful"),
]


def explain_rejection() -> str:
    return "(No story: the lure is not a safe, gentle bedtime-style problem for this setup.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for lid, l in LURES.items():
        lines.append(asp.fact("lure", lid))
        lines.append(asp.fact("risk", lid, l.risk))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for cid, c in enumerate(COMFORTS):
        lines.append(asp.fact("comfort", c.id))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
        for s in sorted(c.soothes):
            lines.append(asp.fact("soothes", c.id, s))
    return "\n".join(lines)


ASP_RULES = r"""
% A lure is relevant in a place if recess happens there.
relevant(P, L) :- affords(P, recess), lure(L).

% Suspenseful stories need a lure, a recess setting, and a prize that can be left behind.
valid(P, L, R) :- relevant(P, L), prize(R), worn_on(R, torso).

% A comfort is compatible when it soothes the risk and helps at the same time.
fix(C, P, L, R) :- valid(P, L, R), soothes(C, lost), covers(C, path).

#show valid/3.
#show fix/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
    ap = argparse.ArgumentParser(
        description="A bedtime-story world about recess, a lure, and suspense."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["teacher"])
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
              and (args.lure is None or c[1] == args.lure)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, lure, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    adult = args.adult or "teacher"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, lure=lure, prize=prize, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], LURES[params.lure], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "gentle"], params.adult)
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
        print(f"{len(combos)} compatible (place, lure, prize) combos:\n")
        for place, lure, prize in combos:
            print(f"  {place:12} {lure:12} {prize}")
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
            header = f"### {p.name}: {p.lure} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
