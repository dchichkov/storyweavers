#!/usr/bin/env python3
"""
A small story world about a ghostly marathon, a lantern-raising challenge,
and a mate who helps the runner learn a lesson.

The tone aims for a soft Ghost Story feel: moonlit, a little eerie, but warm
and child-friendly. The core arc is:

- a ghostly runner wants to finish a marathon,
- a teammate ("mate") gets worried about a steep hill and a raised banner,
- the runner listens to an inner monologue, learns a lesson about pacing,
- the ending is happy and calm.

This file is self-contained and follows the storyworld contract.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit track"
    indoors: bool = False
    hush: str = "The night was quiet, with pale fog lying low."


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    worry: str
    inner: str
    lesson: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Content registry
# ---------------------------------------------------------------------------

SETTINGS = {
    "track": Setting(place="the moonlit track", indoors=False),
    "bridge": Setting(place="the old stone bridge", indoors=False),
    "hall": Setting(place="the echoing hall", indoors=True, hush="The hall was dim, and every footstep sounded soft."),
}

CHALLENGES = {
    "marathon": Challenge(
        id="marathon",
        verb="finish the marathon",
        gerund="running the marathon",
        worry="the runner was pushing too hard",
        inner="Maybe I should slow down and listen to my breath.",
        lesson="going slowly at the right time can help you go farther",
        risk="a stumble from rushing too fast",
        keyword="marathon",
        tags={"run", "race", "lesson"},
    ),
    "raise": Challenge(
        id="raise",
        verb="raise the lantern high",
        gerund="raising the lantern",
        worry="the lantern looked heavy in the dark",
        inner="I can lift it carefully, one steady step at a time.",
        lesson="careful hands can still do brave things",
        risk="dropping the lantern in the fog",
        keyword="raise",
        tags={"light", "lesson"},
    ),
    "mate": Challenge(
        id="mate",
        verb="help the mate cross the bridge",
        gerund="helping a mate",
        worry="the mate seemed lonely in the cold mist",
        inner="A good mate notices when someone needs a friend.",
        lesson="being kind to a mate can make the dark feel smaller",
        risk="leaving a friend behind",
        keyword="mate",
        tags={"friend", "lesson"},
    ),
}

PRIZES = {
    "ribbon": Prize(label="ribbon", phrase="a silver ribbon", type="ribbon", region="hands"),
    "lantern": Prize(label="lantern", phrase="a paper lantern with a star on it", type="lantern", region="hands"),
    "coat": Prize(label="coat", phrase="a warm blue coat", type="coat", region="torso"),
}

GEAR = {
    "pacing": Gear(id="pacing", label="a slower pace", helps={"marathon"}, prep="take a slower pace", tail="slowed down and listened to their breathing"),
    "gloves": Gear(id="gloves", label="soft gloves", helps={"raise"}, prep="put on soft gloves first", tail="lifted the lantern carefully"),
    "lantern-string": Gear(id="lantern-string", label="a long string", helps={"raise"}, prep="tie a long string to the lantern", tail="held the string with steady hands"),
    "handhold": Gear(id="handhold", label="a gentle handhold", helps={"mate"}, prep="walk side by side and hold hands", tail="kept the mate close"),
}

NAMES = ["Mira", "Eli", "Nina", "Theo", "Luna", "Owen", "Asha", "Pip"]
GHOST_NAMES = ["Moss", "Wren", "Iris", "Jules", "Bram", "Nell"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    mate_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def challenge_needs_gear(ch: Challenge, prize: Prize) -> bool:
    if ch.id == "marathon":
        return prize.type in {"ribbon", "coat"}
    if ch.id == "raise":
        return prize.type == "lantern"
    if ch.id == "mate":
        return prize.type in {"coat", "ribbon"}
    return False


def select_gear(ch: Challenge, prize: Prize) -> Optional[Gear]:
    if ch.id == "marathon":
        return GEAR["pacing"]
    if ch.id == "raise":
        return GEAR["gloves"] if prize.type == "lantern" else None
    if ch.id == "mate":
        return GEAR["handhold"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for ch_id, ch in CHALLENGES.items():
            for prize_id, prize in PRIZES.items():
                if challenge_needs_gear(ch, prize) and select_gear(ch, prize):
                    out.append((place, ch_id, prize_id))
    return out


def explain_rejection(ch: Challenge, prize: Prize) -> str:
    return (
        f"(No story: {ch.verb} does not sensibly match {prize.label} in this little world.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, mate: Entity) -> None:
    world.say(
        f"{hero.id} was a little ghost who liked quiet roads, soft fog, and the idea of going far."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a mate named {mate.id}, and the two of them were never afraid of the dark."
    )


def setup_prize(world: World, hero: Entity, prize: Entity, ch: Challenge) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {ch.gerund}, and {hero.pronoun('possessive')} {prize.label} glimmered faintly like moonlight."
    )


def inner_monologue(world: World, hero: Entity, ch: Challenge) -> None:
    hero.memes["thought"] = hero.memes.get("thought", 0.0) + 1
    world.say(
        f"Inside {hero.pronoun('possessive')} quiet head, {hero.id} thought, \"{ch.inner}\""
    )


def worry_turn(world: World, hero: Entity, mate: Entity, ch: Challenge, prize: Entity) -> None:
    hero.memes["tension"] = hero.memes.get("tension", 0.0) + 1
    mate.memes["worry"] = mate.memes.get("worry", 0.0) + 1
    world.say(world.setting.hush)
    world.say(
        f"Then {hero.id} wanted to {ch.verb}, but {mate.id} looked up and saw {ch.worry}."
    )
    world.say(
        f"{mate.id} whispered, \"Careful now. I don't want {ch.risk}.\""
    )


def offer_gear(world: World, hero: Entity, mate: Entity, ch: Challenge, prize: Entity) -> Optional[Gear]:
    gear = select_gear(ch, prize)
    if gear is None:
        return None
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{mate.id} smiled and offered {gear.label}; then {hero.id} could {gear.prep}."
    )
    return gear


def resolution(world: World, hero: Entity, mate: Entity, ch: Challenge, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0.0) + 1
    hero.memes["tension"] = 0.0
    world.say(
        f"{hero.id} listened, and the strange cold worry in {hero.pronoun('possessive')} chest melted away."
    )
    world.say(
        f"They went on together, and soon {hero.id} had learned that {ch.lesson}."
    )
    world.say(
        f"In the end, {hero.id} {gear.tail}, and {prize.label} stayed bright and safe."
    )
    world.say(
        f"{mate.id} laughed softly, and the night felt kind at last."
    )


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize, name: str, mate_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="ghost", type="ghost"))
    mate = world.add(Entity(id=mate_name, kind="ghost", type="ghost"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    intro(world, hero, mate)
    world.para()
    setup_prize(world, hero, prize, challenge)
    inner_monologue(world, hero, challenge)
    world.para()
    worry_turn(world, hero, mate, challenge, prize)
    gear = offer_gear(world, hero, mate, challenge, prize)
    if gear is None:
        raise StoryError(explain_rejection(challenge, prize))
    world.para()
    resolution(world, hero, mate, challenge, prize, gear)
    world.facts.update(hero=hero, mate=mate, prize=prize, challenge=challenge, gear=gear, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a soft ghost story about a character who wants to {f["challenge"].verb} and learns a lesson.',
        f'Tell a child-friendly spooky story with a quiet inner monologue, a mate, and the word "{f["challenge"].keyword}".',
        f'Write a happy-ending story set at {f["setting"].place} where a ghostly mate helps with {f["challenge"].gerund}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    prize: Entity = f["prize"]
    ch: Challenge = f["challenge"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {ch.verb}.",
        ),
        QAItem(
            question=f"Who was {hero.id}'s mate in the story?",
            answer=f"{mate.id} was {hero.id}'s mate, and they stayed together through the spooky night.",
        ),
        QAItem(
            question=f"What did {mate.id} offer to help with?",
            answer=f"{mate.id} offered {gear.label} so {hero.id} could keep going safely.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {ch.lesson}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id}, {mate.id}, and {prize.label} safe in the moonlight.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ch: Challenge = f["challenge"]
    out: list[QAItem] = []
    if "run" in ch.tags:
        out.append(QAItem(
            question="What is a marathon?",
            answer="A marathon is a very long running race that takes a lot of effort and steady pacing.",
        ))
    if "light" in ch.tags:
        out.append(QAItem(
            question="Why might someone raise a lantern?",
            answer="Someone might raise a lantern to hold the light up higher so they can see the path better.",
        ))
    if "friend" in ch.tags:
        out.append(QAItem(
            question="What is a mate?",
            answer="A mate is a friend or companion who stays near and helps when things feel hard.",
        ))
    out.append(QAItem(
        question="What does it mean to learn a lesson?",
        answer="It means understanding something new from what happened, so you can do better next time.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A challenge/prize pair is valid if the challenge needs gear and the gear exists.
valid(Place, Ch, Prize) :- setting(Place), challenge(Ch), prize(Prize),
                           needs_gear(Ch, Prize), has_gear(Ch, Prize).

% Declare that a challenge needs a gearable fix.
needs_gear(marathon, Prize) :- prize_kind(Prize, ribbon).
needs_gear(marathon, Prize) :- prize_kind(Prize, coat).
needs_gear(raise, Prize)    :- prize_kind(Prize, lantern).
needs_gear(mate, Prize)     :- prize_kind(Prize, coat).
needs_gear(mate, Prize)     :- prize_kind(Prize, ribbon).

has_gear(marathon, Prize) :- prize_kind(Prize, ribbon).
has_gear(marathon, Prize) :- prize_kind(Prize, coat).
has_gear(raise, Prize)    :- prize_kind(Prize, lantern).
has_gear(mate, Prize)     :- prize_kind(Prize, coat).
has_gear(mate, Prize)     :- prize_kind(Prize, ribbon).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for ch_id, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", ch_id))
        lines.append(asp.fact("challenge_keyword", ch_id, ch.keyword))
    for pr_id, pr in PRIZES.items():
        lines.append(asp.fact("prize", pr_id))
        lines.append(asp.fact("prize_kind", pr_id, pr_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghostly marathon story world with a mate, a raise, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--challenge", choices=CHALLENGES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, ch_id, pr_id = rng.choice(sorted(filtered))
    name = args.name or rng.choice(NAMES)
    mate_name = args.mate_name or rng.choice([n for n in GHOST_NAMES if n != name])
    return StoryParams(place=place, challenge=ch_id, prize=pr_id, name=name, mate_name=mate_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], PRIZES[params.prize], params.name, params.mate_name)
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
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
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
    StoryParams(place="track", challenge="marathon", prize="ribbon", name="Mira", mate_name="Wren"),
    StoryParams(place="bridge", challenge="mate", prize="coat", name="Nina", mate_name="Iris"),
    StoryParams(place="hall", challenge="raise", prize="lantern", name="Theo", mate_name="Jules"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, ch, prize in combos:
            print(f"  {place:7} {ch:9} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.challenge} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
