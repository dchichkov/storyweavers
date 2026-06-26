#!/usr/bin/env python3
"""
A small storyworld of a mythic court where kindness can mend a hard decree.

The seed tale imagined here is simple:
A young herald comes to a bright court with a troubling message. The queen's
hall is proud, the people's need is great, and a single act of kindness changes
what the court thinks power is for. The storyworld models that change as a
stateful turn: honor is tested, kindness is chosen, and the court ends in
blessing rather than pride.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld
- typed entities with meters and memes
- state-driven narration
- ASP twin for reasonableness checks
- generate / emit / main interface
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"queen", "princess", "girl", "woman", "lady"}
        male = {"king", "prince", "boy", "man", "lord", "herald"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Court:
    name: str
    place: str
    custom: str
    law: str
    honor: str
    wealth: str
    needs: str
    audience_day: str = "moonrise"


@dataclass
class Crown:
    label: str
    phrase: str
    type: str = "crown"
    worn_on: str = "head"
    splashes: set[str] = field(default_factory=lambda: {"doubt", "cold"})
    guards: set[str] = field(default_factory=lambda: {"rain", "dust"})


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    owner_kind: str
    blessed: bool = False
    meters: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, court: Court) -> None:
        self.court = court
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        clone = World(self.court)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def join_sentences(*parts: str) -> str:
    return " ".join(p for p in parts if p)


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def capitalized(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _r_cold_spirit(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("coldness", 0.0) >= THRESHOLD and not e.memes.get("comforted", 0.0):
            sig = ("cold_spirit", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["isolation"] = e.memes.get("isolation", 0.0) + 1
            out.append(f"{e.id} felt alone under the high stone roof.")
    return out


def _r_kindness_blessing(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness_blessing", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["grace"] = e.memes.get("grace", 0.0) + 1
        out.append(f"Kindness made {e.id} brighter than gold.")
    return out


def _r_court_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved"):
        sig = ("court_soften", world.court.name)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("Even the court's walls seemed less hard after that.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_cold_spirit, _r_kindness_blessing, _r_court_soften):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    court: str
    hero: str
    hero_type: str
    ruler: str
    ruler_type: str
    relic: str
    need: str
    seed: Optional[int] = None


COURTS = {
    "sunhall": Court(
        name="Sunhall",
        place="the bright court",
        custom="old banners and careful bows",
        law="the ruler listens only after the herald speaks",
        honor="golden",
        wealth="full of lamps and polished cups",
        needs="the people wait outside the gate for bread",
        audience_day="sunrise",
    ),
    "moonstep": Court(
        name="Moonstep",
        place="the silver court",
        custom="quiet steps and moon-white cloaks",
        law="no decree may be sealed before the poorer are heard",
        honor="cool",
        wealth="full of silver bowls and singing fountains",
        needs="the winter stores are thin",
        audience_day="moonrise",
    ),
}

RELICS = {
    "bread": Relic(label="bread", phrase="warm bread loaves", type="bread", owner_kind="people"),
    "cloak": Relic(label="cloak", phrase="a traveling cloak", type="cloak", owner_kind="herald"),
    "lantern": Relic(label="lantern", phrase="a small lantern", type="lantern", owner_kind="court"),
    "ring": Relic(label="ring", phrase="an old ring of office", type="ring", owner_kind="ruler"),
}

KIND_ACTS = {
    "share": "shared the last bread with the waiting children",
    "listen": "listened to the poorest voices before speaking of law",
    "forgive": "forgave the insult instead of answering with pride",
    "guide": "guided the lost traveler through the gate with a lantern",
}

NAMES = ["Ari", "Mira", "Nolan", "Sera", "Tavi", "Lina", "Cai", "Rhea"]
RULERS = [("queen", "queen"), ("king", "king")]
KINDS = ["kind", "gentle", "brave", "patient", "earnest"]


def court_reasonable(court: Court, need: str, relic: Relic) -> bool:
    if need == "bread" and relic.label != "bread":
        return False
    if need == "winter" and relic.label not in {"cloak", "lantern"}:
        return False
    return True


def explain_rejection(court: Court, need: str, relic: Relic) -> str:
    return (
        f"(No story: in {court.name}, the need for {need} cannot be honestly eased by "
        f"{relic.phrase}. Choose a relic that fits the need.)"
    )


def tell(params: StoryParams) -> World:
    court = COURTS[params.court]
    world = World(court)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    ruler = world.add(Entity(id="Ruler", kind="character", type=params.ruler_type, label=params.ruler))
    relic_def = RELICS[params.relic]
    relic = world.add(Entity(
        id="Relic",
        kind="thing",
        type=relic_def.type,
        label=relic_def.label,
        phrase=relic_def.phrase,
        owner=hero.id,
    ))

    world.say(f"At {court.name}, there was a {court.place} where {court.custom}.")
    world.say(f"The law there said that {court.law}.")
    world.say(
        f"One morning at {court.audience_day}, {hero.id} came before the court carrying "
        f"{article(relic.label)} {relic.label}."
    )
    world.say(
        f"{hero.id} was {article(params.hero_type)} {params.hero_type} known for being "
        f"{params.need} and for a heart that could become kind."
    )

    world.para()
    world.say(
        f"The ruler sat beneath a high carved arch, and the hall was {court.wealth}."
    )
    world.say(
        f"Outside the gate, {court.needs}."
    )
    hero.memes["duty"] = 1
    ruler.memes["authority"] = 1

    if params.need == "bread":
        world.say(f"{hero.id} saw that the people were hungry.")
        world.say(f"{hero.id} remembered the {relic.label} and stepped closer to the throne.")
        world.say(f"Then {hero.id} chose kindness and {KIND_ACTS['share']}.")
        hero.memes["kindness"] = 1
        relic.meters["given"] = 1
        world.facts["resolution"] = "shared"
        world.facts["resolved"] = True
        propagate(world, narrate=True)
        world.para()
        world.say(
            f"The ruler's stern mouth softened, because the court had learned that a gift given in need is stronger than a boast."
        )
        world.say(
            f"By night, the gate stood open, and the children ate warm bread while the court glowed like a small sun."
        )
    else:
        world.say(f"The court was quiet, but the need for the season was still sharp.")
        world.say(f"{hero.id} did not brag; {hero.id} listened, and that listening itself became kind.")
        hero.memes["kindness"] = 1
        world.facts["resolution"] = "listened"
        world.facts["resolved"] = True
        propagate(world, narrate=True)
        world.para()
        world.say(
            f"The ruler answered with mercy, and what had been a hard court became a gentle one."
        )
        world.say(
            f"In the end, {hero.id} left with an open path and a blessing that outshone the ring of office."
        )

    world.facts.update(
        hero=hero,
        ruler=ruler,
        relic=relic,
        court=court,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story for children about {f["hero"].id} at {f["court"].name} where kindness changes the court.',
        f"Tell a gentle court myth in which {f['hero'].id} brings {f['relic'].phrase} and learns that kindness matters more than pride.",
        "Write a story with a royal court, a small hard need, and a kind choice that blesses everyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ruler = f["ruler"]
    relic = f["relic"]
    court = f["court"]
    qa = [
        QAItem(
            question=f"Who came to {court.name} with {relic.phrase}?",
            answer=f"{hero.id} came to {court.name} carrying {relic.phrase}.",
        ),
        QAItem(
            question=f"What did the ruler do before the story turned gentler?",
            answer=f"{ruler.id.capitalize()} sat beneath the arch and listened as the court stayed quiet.",
        ),
        QAItem(
            question=f"What changed the court in the end?",
            answer=f"Kindness changed the court. {hero.id} chose a kind act instead of pride, and the court became gentler.",
        ),
    ]
    if world.facts.get("resolution") == "shared":
        qa.append(QAItem(
            question=f"What did {hero.id} do with the bread?",
            answer=f"{hero.id} shared the last bread with the waiting children, and that made the ruler soften.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did {hero.id} show kindness?",
            answer=f"{hero.id} showed kindness by listening first and letting the court hear the poorer voices.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a court?",
            answer="A court is the place where a ruler meets people, hears petitions, and makes important choices.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, comfort, or share with others instead of being harsh or selfish.",
        ),
        QAItem(
            question="Why do myths often feel grand?",
            answer="Myths often feel grand because they use big places, strong feelings, and important choices that seem larger than ordinary life.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_fact(H).
ruler(R) :- ruler_fact(R).
relic(X) :- relic_fact(X).
kindness_possible(H) :- hero_fact(H).
resolved(shared) :- choice(shared).
resolved(listened) :- choice(listened).
good_story :- hero_fact(H), ruler_fact(R), kindness_possible(H), resolved(_), court_fact(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in COURTS.values():
        lines.append(asp.fact("court_fact", c.name))
    for r in RELICS.values():
        lines.append(asp.fact("relic_fact", r.label))
    for n in NAMES:
        lines.append(asp.fact("hero_fact", n))
    for r, _ in RULERS:
        lines.append(asp.fact("ruler_fact", r))
    lines.append(asp.fact("choice", "shared"))
    lines.append(asp.fact("choice", "listened"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    ok = any(sym.name == "good_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes a good mythic court story.")
        return 0
    print("MISMATCH: ASP twin failed to recognize a good story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic court storyworld centered on kindness.")
    ap.add_argument("--court", choices=sorted(COURTS))
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--hero-type", choices=["herald", "girl", "boy", "child"])
    ap.add_argument("--ruler", choices=["queen", "king"])
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--need", choices=["bread", "winter"])
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
    court = args.court or rng.choice(sorted(COURTS))
    need = args.need or rng.choice(["bread", "winter"])
    if need == "bread":
        relic_choices = ["bread"]
    else:
        relic_choices = ["cloak", "lantern"]
    relic = args.relic or rng.choice(relic_choices)
    if args.relic and not court_reasonable(COURTS[court], need, RELICS[args.relic]):
        raise StoryError(explain_rejection(COURTS[court], need, RELICS[args.relic]))
    if not court_reasonable(COURTS[court], need, RELICS[relic]):
        raise StoryError(explain_rejection(COURTS[court], need, RELICS[relic]))
    hero = args.hero or rng.choice(NAMES)
    hero_type = args.hero_type or "herald"
    ruler = args.ruler or rng.choice(["queen", "king"])
    return StoryParams(court=court, hero=hero, hero_type=hero_type, ruler=ruler, ruler_type=ruler, relic=relic, need=need)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/0."))
        print("ASP model atoms:")
        for sym in model:
            print(sym)
        return

    samples: list[StorySample] = []
    if args.all:
        for court in sorted(COURTS):
            for need in ["bread", "winter"]:
                params = StoryParams(
                    court=court,
                    hero="Ari" if court == "sunhall" else "Mira",
                    hero_type="herald",
                    ruler="queen",
                    ruler_type="queen",
                    relic="bread" if need == "bread" else "cloak",
                    need=need,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.court}: {p.hero} / {p.need}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
