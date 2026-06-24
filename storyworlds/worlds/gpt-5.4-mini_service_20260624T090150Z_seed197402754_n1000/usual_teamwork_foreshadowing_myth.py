#!/usr/bin/env python3
"""
A standalone story world for a tiny mythic tale about the usual teamwork
that brings a foretold change.

Premise:
- A small village faces a repeating, ordinary task: each morning, a heavy gate
  must be raised before the path can be used.
- The gate is old, stubborn, and a little magical in a quiet myth-like way.
- A helpful sign, omen, or repeated clue foreshadows what must be done.
- The story turns when the characters finally work together in the usual,
  practical way, proving the omen true.

This world is built to generate short, child-facing stories with:
- a clear beginning, middle turn, and ending image
- physically modeled objects and emotionally modeled characters
- a reasonableness gate for the central problem/fix pair
- an inline ASP twin for parity checking
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    can_lift: bool = False
    can_notice: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
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
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    verb: str
    gerund: str
    sign: str
    omen: str
    risk_meter: str
    route: str
    place_needed: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    requires: set[str]
    carry: str
    finish: str
    plural: bool = False


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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village": Setting(place="the village square", sky="morning", affords={"raise_gate"}),
    "bridge": Setting(place="the old bridge", sky="dawn", affords={"raise_gate"}),
    "harbor": Setting(place="the harbor path", sky="dawn", affords={"raise_gate"}),
}

CHALLENGES = {
    "gate": Challenge(
        id="gate",
        label="the stone gate",
        verb="raise the stone gate",
        gerund="raising the stone gate",
        sign="the bell gave one low ring",
        omen="the rope creaked before anyone touched it",
        risk_meter="heavy",
        route="pull the rope together",
        place_needed="the gate winch",
        clue="the old marks on the rope showed where hands had once pulled together",
        tags={"gate", "stone", "rope"},
    ),
    "barrier": Challenge(
        id="barrier",
        label="the river barrier",
        verb="lift the river barrier",
        gerund="lifting the river barrier",
        sign="the water tapped three times against the posts",
        omen="the wooden lever shivered in the dawn",
        risk_meter="stuck",
        route="push the lever together",
        place_needed="the lever",
        clue="fresh scratches showed the lever was meant for two hands",
        tags={"barrier", "river", "lever"},
    ),
    "door": Challenge(
        id="door",
        label="the temple door",
        verb="open the temple door",
        gerund="opening the temple door",
        sign="the candle flame bent toward the latch",
        omen="the bronze latch was cold in the first light",
        risk_meter="stiff",
        route="turn the latch together",
        place_needed="the bronze latch",
        clue="the latch had two worn grips, one on each side",
        tags={"door", "temple", "latch"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="the braided rope",
        phrase="a braided rope with soft grips",
        helps_with={"gate"},
        requires={"gate"},
        carry="held the rope at once",
        finish="the rope settled back into its hook",
    ),
    "lever": Aid(
        id="lever",
        label="the long lever",
        phrase="a long lever carved from ash wood",
        helps_with={"barrier"},
        requires={"barrier"},
        carry="rested their hands on the lever together",
        finish="the lever came down with a steady sigh",
    ),
    "keys": Aid(
        id="keys",
        label="the bronze keys",
        phrase="a ring of bronze keys",
        helps_with={"door"},
        requires={"door"},
        carry="shared the keys between both hands",
        finish="the keys turned with a bright little click",
    ),
}

PEOPLE = {
    "boy": ["Niko", "Oren", "Milo", "Ivo", "Tarin"],
    "girl": ["Ari", "Lena", "Mira", "Sela", "Tova"],
    "elder": ["Grandmother", "Grandfather"],
}

TRAITS = ["quiet", "kind", "patient", "brave", "gentle", "steady", "usual"]
OMENS = [
    "a bird landed on the sign and sang once",
    "dust swirled in a small circle at the gate",
    "the shadow of the tower pointed at the rope",
    "the wind lifted only the frayed end of the cord",
]

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    challenge: str
    aid: str
    child_name: str
    child_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

class StoryWorldError(StoryError):
    pass


def _character_intro(world: World, hero: Entity, elder: Entity, challenge: Challenge) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was known as a {hero.meters.get('age', 0) or 'small'} "
        f"{hero.type} who liked the usual morning work."
    )
    world.say(
        f"{elder.id} had watched the old {challenge.label} for many seasons, and {hero.id} always listened."
    )


def _foreshadow(world: World, challenge: Challenge) -> None:
    world.say(
        f"That morning, {challenge.sign}. {challenge.omen}. "
        f"It felt like a little warning from the old place itself."
    )


def _want(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(f"{hero.id} wanted to {challenge.verb}, just as {hero.id} had seen the grown-ups do before.")


def _predict_risk(world: World, challenge: Challenge) -> bool:
    # In this mythic world, the physical risk is simple: the gate is heavy/stuck/stiff.
    return True


def _warn(world: World, elder: Entity, hero: Entity, challenge: Challenge) -> None:
    world.say(
        f'"Careful," said {elder.id}. "When {challenge.omen}, it usually means '
        f"{challenge.label} will need more than one set of hands.""
    )


def _unready(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["impatience"] = hero.memes.get("impatience", 0) + 1
    world.say(f"{hero.id} reached for {challenge.place_needed}, but it would not move for one small hand alone.")


def _teamup(world: World, hero: Entity, elder: Entity, challenge: Challenge, aid: Aid) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    elder.memes["care"] = elder.memes.get("care", 0) + 1
    world.say(
        f"Then {elder.id} smiled and showed the usual answer: {aid.label}. "
        f"Together, they {aid.carry}."
    )


def _resolve(world: World, hero: Entity, elder: Entity, challenge: Challenge, aid: Aid) -> None:
    world.say(
        f"{challenge.label} moved at last. {aid.finish}. "
        f"{hero.id} could cross the way, and the morning path opened like a small blessing."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    elder.memes["joy"] = elder.memes.get("joy", 0) + 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def challenge_needs_teamwork(challenge: Challenge) -> bool:
    return challenge.id in {"gate", "barrier", "door"}


def aid_fits(challenge: Challenge, aid: Aid) -> bool:
    return challenge.id in aid.helps_with and challenge.id in aid.requires


def valid_combo(setting: Setting, challenge: Challenge, aid: Aid) -> bool:
    return "raise_gate" in setting.affords and challenge_needs_teamwork(challenge) and aid_fits(challenge, aid)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for cid, challenge in CHALLENGES.items():
            for aid_id, aid in AIDS.items():
                if valid_combo(setting, challenge, aid):
                    out.append((sid, cid, aid_id))
    return out


def explain_rejection(challenge: Challenge, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} does not match {challenge.label}. "
        f"The tale needs a fix that genuinely helps with {challenge.route}, "
        f"so this pair is not reasonable.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(village). setting(bridge). setting(harbor).
affords(village,raise_gate). affords(bridge,raise_gate). affords(harbor,raise_gate).

challenge(gate). challenge(barrier). challenge(door).

aid(rope). aid(lever). aid(keys).

needs(gate,rope). helps(gate,rope).
needs(barrier,lever). helps(barrier,lever).
needs(door,keys). helps(door,keys).

valid(S,C,A) :- affords(S,raise_gate), challenge(C), aid(A), needs(C,A), helps(C,A).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for aff in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, aff))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    for cid, aid in [("gate", "rope"), ("barrier", "lever"), ("door", "keys")]:
        lines.append(asp.fact("needs", cid, aid))
        lines.append(asp.fact("helps", cid, aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

GIRL_NAMES = PEOPLE["girl"]
BOY_NAMES = PEOPLE["boy"]
ELDER_NAMES = {"elder": ["Grandmother", "Grandfather"]}


def build_story(world: World, hero: Entity, elder: Entity, challenge: Challenge, aid: Aid) -> None:
    _character_intro(world, hero, elder, challenge)
    world.para()
    _foreshadow(world, challenge)
    _want(world, hero, challenge)
    _warn(world, elder, hero, challenge)
    _unready(world, hero, challenge)
    world.para()
    _teamup(world, hero, elder, challenge, aid)
    _resolve(world, hero, elder, challenge, aid)


def tell(setting: Setting, challenge: Challenge, aid: Aid, child_name: str, child_type: str, elder_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    elder_name = "Grandmother" if elder_type == "grandmother" else "Grandfather"
    elder = world.add(Entity(id=elder_name, kind="character", type="elder", label=elder_name))
    challenge_ent = world.add(Entity(id=challenge.id, type="thing", label=challenge.label, phrase=challenge.label))
    aid_ent = world.add(Entity(id=aid.id, type="thing", label=aid.label, phrase=aid.phrase, plural=aid.plural))

    hero.meters["small"] = 1
    hero.memes["trait"] = 1
    world.facts.update(
        hero=hero,
        elder=elder,
        challenge=challenge_ent,
        aid=aid_ent,
        trait=trait,
        setting=setting,
        challenge_cfg=challenge,
        aid_cfg=aid,
    )
    build_story(world, hero, elder, challenge, aid)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["challenge_cfg"]
    a = f["aid_cfg"]
    h = f["hero"]
    return [
        f'Write a short myth-like story for a child about the usual way to {c.verb} when an omen appears.',
        f"Tell a gentle story where {h.id} notices a sign, learns that {c.label} needs teamwork, and uses {a.label}.",
        f'Write a small story with foreshadowing and teamwork that includes the phrase "usual answer".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    c = f["challenge_cfg"]
    a = f["aid_cfg"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {c.verb}.",
        ),
        QAItem(
            question=f"What sign hinted that something important was coming?",
            answer=f"The story foreshadowed the change with a clue: {c.sign}.",
        ),
        QAItem(
            question=f"What was the usual way to solve the problem with {c.label}?",
            answer=f"The usual way was teamwork. {hero.id} and {elder.id} used {a.label} together.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"In the end, {c.label} moved and {hero.id} could cross the way safely.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["challenge_cfg"]
    a = f["aid_cfg"]
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together to do something that is hard for one person alone.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important will happen later in the story.",
        ),
        QAItem(
            question=f"Why is {a.label} useful in stories like this?",
            answer=f"{a.label} is useful because it helps solve the problem with {c.label}.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    challenge: str
    aid: str
    child_name: str
    child_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="village", challenge="gate", aid="rope", child_name="Niko", child_type="boy", elder_type="grandmother", trait="usual"),
    StoryParams(setting="bridge", challenge="barrier", aid="lever", child_name="Mira", child_type="girl", elder_type="grandfather", trait="steady"),
    StoryParams(setting="harbor", challenge="door", aid="keys", child_name="Tova", child_type="girl", elder_type="grandmother", trait="quiet"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.aid:
        ch = CHALLENGES[args.challenge]
        aid = AIDS[args.aid]
        if not valid_combo(SETTINGS[args.setting] if args.setting else SETTINGS["village"], ch, aid):
            raise StoryError(explain_rejection(ch, aid))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, challenge_id, aid_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        challenge=challenge_id,
        aid=aid_id,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CHALLENGES[params.challenge],
        AIDS[params.aid],
        params.child_name,
        params.child_type,
        params.elder_type,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small myth-like story world about usual teamwork and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
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
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, c, a in combos:
            print(f"  {s:8} {c:8} {a:8}")
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
            header = f"### {p.child_name}: {p.challenge} in {p.setting} (aid: {p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
