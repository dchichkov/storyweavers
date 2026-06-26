#!/usr/bin/env python3
"""
storyworlds/worlds/civil_ize_bravery_pirate_tale.py
====================================================

A small pirate-tale story world about bravery, manners, and a civil-ize turn:
a crew faces a noisy trouble, the captain warns them, and a brave compromise
helps everyone act with more kindness and less bluster.

The domain is intentionally tiny and classical:
- one captain, one young pirate, one pressing problem
- emotional state drives the prose
- a brave, civilizing choice resolves the tension
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the harbor"
    vibe: str = "salt wind and creaking ropes"


@dataclass
class Trouble:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tag: str


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    turns: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": Setting(place="the harbor", vibe="salt wind and creaking ropes"),
    "dock": Setting(place="the dock", vibe="wet boards and gull cries"),
    "cove": Setting(place="the cove", vibe="foam, shells, and moon-bright water"),
}

TROUBLES = {
    "splash": Trouble(
        id="splash",
        verb="splash about",
        gerund="splashing about",
        rush="run to the water and kick up a mess",
        mess="wet",
        soil="soaking wet",
        tag="water",
    ),
    "mud": Trouble(
        id="mud",
        verb="stomp in the mud",
        gerund="stomping in mud",
        rush="dash into the muddy bank",
        mess="muddy",
        soil="splotched with mud",
        tag="mud",
    ),
    "paint": Trouble(
        id="paint",
        verb="paint the ship sign",
        gerund="painting the ship sign",
        rush="grab the paint pots at once",
        mess="painted",
        soil="spattered with paint",
        tag="paint",
    ),
}

REMEDIES = {
    "boots": Remedy(
        id="boots",
        label="sea boots",
        prep="put on the sea boots",
        tail="trotted back out in the sea boots",
        guards={"wet", "muddy"},
        turns={"feet"},
        plural=True,
    ),
    "apron": Remedy(
        id="apron",
        label="a tar apron",
        prep="tie on a tar apron",
        tail="came back with the tar apron tied snug",
        guards={"painted"},
        turns={"torso"},
    ),
    "cloak": Remedy(
        id="cloak",
        label="a dry cloak",
        prep="wrap a dry cloak around the shoulders",
        tail="returned with the dry cloak snug around the shoulders",
        guards={"wet"},
        turns={"torso"},
    ),
}

NAMES = ["Mia", "Nora", "Finn", "Theo", "Lina", "Bea", "Jax", "Iris"]
TRAITS = ["bold", "cheery", "stubborn", "bright-eyed", "spry"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    remedy: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def trouble_at_risk(trouble: Trouble, remedy: Remedy) -> bool:
    return bool(trouble.tag in remedy.guards or trouble.mess in remedy.guards)


def select_remedy(trouble: Trouble) -> Optional[Remedy]:
    for rem in REMEDIES.values():
        if trouble.mess in rem.guards:
            return rem
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for t_id, t in TROUBLES.items():
            for r_id, r in REMEDIES.items():
                if trouble_at_risk(t, r):
                    combos.append((s, t_id, r_id))
    return combos


# ---------------------------------------------------------------------------
# Narrative mechanics
# ---------------------------------------------------------------------------

def _do_trouble(world: World, actor: Entity, trouble: Trouble, narrate: bool = True) -> None:
    actor.meters[trouble.mess] = actor.meters.get(trouble.mess, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    world.zone = {"feet", "torso"} if trouble.mess == "wet" else {"feet"} if trouble.mess == "muddy" else {"torso"}
    if narrate:
        world.say(f"{actor.id} did {trouble.gerund}.")


def predict_mess(world: World, hero: Entity, trouble: Trouble, prize_id: str) -> dict:
    sim = world.copy()
    _do_trouble(sim, sim.get(hero.id), trouble, narrate=False)
    prize = sim.entities[prize_id]
    soiled = False
    if trouble.mess == "wet" and prize.worn_by == hero.id and prize.label in {"coat", "cloak"}:
        soiled = True
    if trouble.mess == "muddy" and prize.worn_by == hero.id and prize.label in {"boots", "shoes"}:
        soiled = True
    if trouble.mess == "painted" and prize.worn_by == hero.id and prize.label in {"shirt", "cloak"}:
        soiled = True
    return {"soiled": soiled, "bravery": hero.memes.get("bravery", 0.0)}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {next((t for t in hero.meters if t), 'young')} pirate with a quick grin.")


def loves(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["longing"] = hero.memes.get("longing", 0.0) + 1.0
    world.say(f"{hero.pronoun().capitalize()} loved {trouble.gerund}, for the harbor felt like a game on windy days.")


def warn(world: World, captain: Entity, hero: Entity, trouble: Trouble, prize: Entity) -> bool:
    pred = predict_mess(world, hero, trouble, prize.id)
    if not pred["soiled"]:
        return False
    captain.memes["care"] = captain.memes.get("care", 0.0) + 1.0
    world.facts["predicted_soil"] = trouble.soil
    world.say(f'"If ye go {trouble.verb}, that {prize.label} will end up {trouble.soil}," said {captain.id}.')
    return True


def defy(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1.0
    world.say(f"{hero.id} wanted the fun too much and rushed toward the trouble anyway.")


def grab_and_turn(world: World, captain: Entity, hero: Entity) -> None:
    hero.memes["caught"] = hero.memes.get("caught", 0.0) + 1.0
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(f"But {captain.id} held up a steady hand and said, 'Bravery can be civil-ize'd, lad.'")


def offer_remedy(world: World, captain: Entity, hero: Entity, trouble: Trouble, prize: Entity) -> Optional[Remedy]:
    rem = select_remedy(trouble)
    if rem is None:
        return None
    if trouble.mess not in rem.guards:
        return None
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(f'"How about we {rem.prep} and then {trouble.verb} proper-like?" asked {captain.id}.')
    return rem


def accept(world: World, hero: Entity, captain: Entity, trouble: Trouble, prize: Entity, rem: Remedy) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["defiance"] = 0.0
    world.say(f"{hero.id}'s face lit up. {hero.pronoun().capitalize()} nodded and hugged {captain.pronoun('object')}.")
    world.say(f"They {rem.tail}. Soon {hero.id} was {trouble.gerund}, and {prize.label} stayed clean and shipshape.")


def tell(setting: Setting, trouble: Trouble, hero_name: str = "Mara", role: str = "matey", trait: str = "bold") -> World:
    world = World(setting)
    captain = world.add(Entity(id="Captain", kind="character", type="captain"))
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", meters={"bravery": 0.0}, memes={"joy": 0.0}))
    prize = world.add(Entity(id="prize", type="shirt", label="shirt", phrase="a white sailor shirt", owner=hero.id, caretaker=captain.id))
    prize.worn_by = hero.id

    hero.meters["bravery"] = 1.0
    introduce(world, hero)
    loves(world, hero, trouble)
    world.say(f"{captain.id} had bought {hero.id} {prize.phrase} for the day.")
    world.say(f"{hero.id} loved the fine shirt and wore it as proudly as a flag.")

    world.para()
    world.say(f"At {setting.place}, the air felt like {setting.vibe}.")
    world.say(f"{hero.id} wanted to {trouble.verb}, but {captain.id} frowned at {prize.label}.")
    warn(world, captain, hero, trouble, prize)
    defy(world, hero, trouble)
    grab_and_turn(world, captain, hero)

    world.para()
    rem = offer_remedy(world, captain, hero, trouble, prize)
    if rem:
        accept(world, hero, captain, trouble, prize, rem)

    world.facts.update(hero=hero, captain=captain, prize=prize, trouble=trouble, remedy=rem, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "water": [("What does it mean for something to be wet?",
               "Wet means covered with water or damp from water.")],
    "mud": [("What is mud?",
             "Mud is soft, wet dirt that can stick to boots and clothes.")],
    "paint": [("Why can paint make a mess?",
               "Paint can make a mess because it is liquid and can drip or smear.")],
    "boots": [("What are boots for?",
               "Boots protect feet and keep them dry or clean in rough weather.")],
    "cloak": [("What is a cloak?",
              "A cloak is a loose outer garment that can help keep you warm and dry.")],
    "apron": [("What is an apron for?",
               "An apron helps protect clothes from spills and splashes.")],
    "bravery": [("What is bravery?",
                 "Bravery means doing something even when you feel worried, scared, or nervous.")],
    "civilize": [("What does it mean to civil-ize behavior?",
                  "To civil-ize behavior is to make it more polite, calmer, and kinder.")],
}

KNOWLEDGE_ORDER = ["bravery", "civilize", "water", "mud", "paint", "boots", "cloak", "apron"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, captain, trouble = f["hero"], f["captain"], f["trouble"]
    return [
        f'Write a short pirate tale about a {hero.pronoun("subject")} named {hero.id} who wants to {trouble.verb}.',
        f"Tell a gentle sea story where {captain.id} helps {hero.id} use bravery in a civil-ize way.",
        f"Write a child-friendly pirate story with a brave choice, a warning, and a safer plan at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, trouble, prize = f["hero"], f["captain"], f["trouble"], f["prize"]
    rem = f.get("remedy")
    place = f["setting"].place

    qa = [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"It is about {hero.id}, a young pirate who loves {trouble.gerund} at {place}.",
        ),
        QAItem(
            question=f"What did {captain.id} warn would happen to the {prize.label}?",
            answer=f"{captain.id} warned that the {prize.label} would end up {trouble.soil}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the safer plan?",
            answer=f"{hero.id} wanted to {trouble.verb}.",
        ),
    ]
    if rem:
        qa.append(
            QAItem(
                question=f"How did the crew keep the {prize.label} safe while still having fun?",
                answer=f"They used {rem.label} first, so {hero.id} could still {trouble.verb} without ruining the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy and brave, because {hero.id} got to play while still keeping things civil and clean.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["trouble"].tag, "bravery", "civilize"}
    if world.facts.get("remedy"):
        tags.add(world.facts["remedy"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
trouble_at_risk(T, R) :- trouble(T), remedy(R), mess_of(T, M), guards(R, M).
valid_combo(S, T, R) :- setting(S), trouble(T), remedy(R), trouble_at_risk(T, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards", rid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# StorySample pipeline
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small civil-ize bravery pirate tale world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--role", default="matey")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.trouble:
        combos = [c for c in combos if c[1] == args.trouble]
    if args.remedy:
        combos = [c for c in combos if c[2] == args.remedy]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, remedy = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, trouble=trouble, remedy=remedy, name=name, role=args.role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TROUBLES[params.trouble], params.name, params.role, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="harbor", trouble="splash", remedy="cloak", name="Mara", role="matey", trait="bold"),
    StoryParams(setting="dock", trouble="mud", remedy="boots", name="Finn", role="deckhand", trait="cheery"),
    StoryParams(setting="cove", trouble="paint", remedy="apron", name="Lina", role="matey", trait="bright-eyed"),
]


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, trouble, remedy) combos:\n")
        for s, t, r in triples:
            print(f"  {s:8} {t:8} {r:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.trouble} at {p.setting} (remedy: {p.remedy})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
