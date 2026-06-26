#!/usr/bin/env python3
"""
A small mythic storyworld about a proud figure, a warning omen, and a mystery
that is solved by a careful act of seizing a hem.

Seed premise:
- Mythic tone
- Foreshadowing
- A mystery to solve
- Seed words: seize, hem, arrogance

The world is built around a village rite in which a young seeker notices signs
of trouble, learns that arrogance can blind a leader, and resolves the mystery
by seizing the hem of a cloak before it is too late.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "seeress", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str = "the temple road"
    kind: str = "road"
    afford: set[str] = field(default_factory=lambda: {"walk", "listen", "seize"})


@dataclass
class Quest:
    id: str
    omen: str
    secret: str
    clue: str
    action: str
    result: str
    danger: str
    keyword: str = "mystery"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "torso"
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


def _r_shiver(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("unease", 0.0) < THRESHOLD:
            continue
        sig = ("shiver", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] = ent.memes.get("fear", 0.0) + 1
        out.append(f"A chill followed {ent.id} like a shadow.")
    return out


def _r_humility(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("arrogance", 0.0) < THRESHOLD:
            continue
        if ent.memes.get("warned", 0.0) < THRESHOLD:
            continue
        sig = ("humble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["arrogance"] = 0.0
        ent.memes["doubt"] = ent.memes.get("doubt", 0.0) + 1
        out.append(f"{ent.id} faltered and heard the old warning at last.")
    return out


CAUSAL_RULES = [
    _r_shiver,
    _r_humility,
]


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


def foreshadow(world: World, seer: Entity, lord: Entity, quest: Quest) -> None:
    seer.meters["unease"] = seer.meters.get("unease", 0.0) + 1
    lord.memes["arrogance"] = lord.memes.get("arrogance", 0.0) + 1
    world.say(
        f"Before dawn, {seer.id} saw an omen: {quest.omen}. "
        f"It seemed to whisper that pride would hide a wound."
    )


def set_out(world: World, hero: Entity, lord: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} walked beside {lord.id} on the temple road, where the stones "
        f"remembered older gods than either of them."
    )
    world.say(
        f"The question followed them: why had {quest.secret} vanished, and what "
        f"had left {quest.clue} behind?"
    )


def boast(world: World, lord: Entity, quest: Quest) -> None:
    lord.memes["arrogance"] = lord.memes.get("arrogance", 0.0) + 1
    world.say(
        f"{lord.id} laughed and said the matter was small, as if a king's word "
        f"could settle every shadow."
    )
    world.say(
        f"But the air tightened, and the old fear returned. {quest.danger} had not "
        f"been answered."
    )


def reveal_clue(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["attention"] = hero.meters.get("attention", 0.0) + 1
    world.say(
        f"{hero.id} knelt and saw {quest.clue} caught at the edge of the altar steps."
    )
    world.say(
        f"It matched the torn border of the sacred cloak, and at once the mystery "
        f"began to take shape."
    )


def seize_hem(world: World, hero: Entity, cloak: Entity, lord: Entity, quest: Quest) -> None:
    if cloak.worn_by != lord.id:
        raise StoryError("the hem can only be seized while the cloak is being worn")
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    cloak.meters["torn"] = cloak.meters.get("torn", 0.0) + 1
    lord.memes["warned"] = lord.memes.get("warned", 0.0) + 1
    propagate(world, narrate=True)
    world.say(
        f"Then {hero.id} reached out and seized the hem of {lord.id}'s cloak, "
        f"stopping the proud march before the next step could break the oath."
    )
    world.say(
        f"At the touch, the secret showed itself: {quest.result}. "
        f"The old sign had not lied."
    )


def resolve(world: World, hero: Entity, lord: Entity, quest: Quest) -> None:
    lord.memes["arrogance"] = 0.0
    lord.memes["gratitude"] = lord.memes.get("gratitude", 0.0) + 1
    hero.memes["honor"] = hero.memes.get("honor", 0.0) + 1
    world.say(
        f"{lord.id} bowed his head at last and thanked {hero.id} for the truth."
    )
    world.say(
        f"The cloak was mended, the hidden crack was bound, and the road lay safe "
        f"again under a calmer sky."
    )


SETTING = Setting()

QUESTS = {
    "temple": Quest(
        id="temple",
        omen="a raven circling the altar three times",
        secret="the sacred bell",
        clue="black wax",
        action="seize",
        result="the bell had been swallowed into a hidden altar chamber",
        danger="the floor might open beneath the procession",
        tags={"raven", "bell", "altar", "cloak"},
    ),
    "river": Quest(
        id="river",
        omen="foam crawling against the current",
        secret="the silver cup",
        clue="river reeds tied in a knot",
        action="seize",
        result="the cup had been hidden in a reed basket beneath the bridge",
        danger="the bridge might not bear the weight of the boastful party",
        tags={"river", "cup", "bridge", "cloak"},
    ),
    "cave": Quest(
        id="cave",
        omen="a torch that burned blue in the cave mouth",
        secret="the stone seal",
        clue="ash on a hem",
        action="seize",
        result="the seal had been carried behind a loose wall",
        danger="the cave wind might snuff the only light",
        tags={"cave", "seal", "torch", "cloak"},
    ),
}

PRIZES = {
    "cloak": Prize(id="cloak", label="cloak", phrase="a woven cloak of dusk", region="torso"),
    "mantle": Prize(id="mantle", label="mantle", phrase="a royal mantle edged in gold", region="torso"),
}

HEROES = [
    ("Ari", "boy", "young seeker"),
    ("Mira", "girl", "young seer"),
    ("Sera", "girl", "apprentice oracle"),
    ("Talan", "boy", "temple child"),
]

LORDS = [
    ("King Oren", "king"),
    ("Queen Ilya", "queen"),
    ("Lord Vara", "man"),
    ("Lady Neris", "woman"),
]


@dataclass
class StoryParams:
    quest: str
    prize: str
    hero: str
    hero_type: str
    hero_role: str
    lord: str
    lord_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: foreshadowing, arrogance, and a mystery to solve.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--lord")
    ap.add_argument("--lord-type", choices=["king", "queen", "man", "woman"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(q, p) for q in QUESTS for p in PRIZES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.quest:
        combos = [c for c in combos if c[0] == args.quest]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if not combos:
        raise StoryError("No valid quest/prize combination matches the given options.")
    quest, prize = rng.choice(sorted(combos))
    hero, hero_type, hero_role = rng.choice(HEROES)
    lord, lord_type = rng.choice(LORDS)
    if args.hero:
        hero = args.hero
    if args.hero_type:
        hero_type = args.hero_type
    if args.lord:
        lord = args.lord
    if args.lord_type:
        lord_type = args.lord_type
    return StoryParams(quest=quest, prize=prize, hero=hero, hero_type=hero_type, hero_role=hero_role, lord=lord, lord_type=lord_type)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    quest = QUESTS[params.quest]
    prize = PRIZES[params.prize]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, traits=["wise", "quiet"]))
    lord = world.add(Entity(id=params.lord, kind="character", type=params.lord_type, traits=["proud"]))
    cloak = world.add(Entity(id=prize.id, type="cloak", label=prize.label, phrase=prize.phrase, owner=lord.id, worn_by=lord.id, region=prize.region))
    world.facts.update(hero=hero, lord=lord, quest=quest, prize=cloak)

    world.say(
        f"In the old days, {hero.id} was known as a {params.hero_role}, "
        f"and {lord.id} wore {cloak.phrase} like a sign of command."
    )
    world.say(
        f"Yet before the tale truly began, there came a foreshadowing: {quest.omen}."
    )

    world.para()
    foreshadow(world, hero, lord, quest)
    set_out(world, hero, lord, quest)
    boast(world, lord, quest)
    reveal_clue(world, hero, quest)

    world.para()
    seize_hem(world, hero, cloak, lord, quest)

    world.para()
    resolve(world, hero, lord, quest)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    hero = world.facts["hero"]
    lord = world.facts["lord"]
    return [
        f"Write a short myth about {hero.id}, a proud ruler, and a warning sign tied to {q.omen}.",
        f"Tell a child-friendly legend where {hero.id} must solve a mystery by seizing a hem.",
        f"Write a mythic story that includes arrogance, foreshadowing, and a hidden truth about {lord.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    lord = world.facts["lord"]
    quest = world.facts["quest"]
    prize = world.facts["prize"]
    return [
        QAItem(
            question=f"Who noticed the omen before the mystery was solved?",
            answer=f"{hero.id} noticed the omen first and understood that it was warning them about the hidden danger.",
        ),
        QAItem(
            question=f"What showed that {lord.id} was being too proud?",
            answer=f"{lord.id} laughed off the warning and acted as if the problem were too small to matter. That was arrogance.",
        ),
        QAItem(
            question=f"What clue helped explain the mystery?",
            answer=f"The clue was {quest.clue}, and it matched the torn edge of the sacred cloak.",
        ),
        QAItem(
            question=f"What did {hero.id} seize to stop the trouble?",
            answer=f"{hero.id} seized the hem of the cloak, and that single careful act stopped the procession long enough to uncover the truth.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {lord.id} thanking {hero.id}, the hidden secret revealed, and the road made safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a hint given early in a story that something important or dangerous may happen later.",
        ),
        QAItem(
            question="What is arrogance?",
            answer="Arrogance is when someone acts as if they are better than everyone else and does not listen well.",
        ),
        QAItem(
            question="What does it mean to seize something?",
            answer="To seize something means to grab it quickly and firmly.",
        ),
        QAItem(
            question="What is a hem?",
            answer="A hem is the edge of cloth, like the bottom border of a cloak or dress.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} worn_by={e.worn_by}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest(Q) :- quest_id(Q).
prize(P) :- prize_id(P).
valid(Q,P) :- quest(Q), prize(P).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for q in QUESTS:
        lines.append(asp.fact("quest_id", q))
    for p in PRIZES:
        lines.append(asp.fact("prize_id", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - asps))
    print("only in clingo:", sorted(asps - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(quest="temple", prize="cloak", hero="Mira", hero_type="girl", hero_role="young seer", lord="King Oren", lord_type="king"),
    StoryParams(quest="river", prize="mantle", hero="Ari", hero_type="boy", hero_role="young seeker", lord="Queen Ilya", lord_type="queen"),
    StoryParams(quest="cave", prize="cloak", hero="Sera", hero_type="girl", hero_role="apprentice oracle", lord="Lord Vara", lord_type="man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.hero} / {p.quest} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
