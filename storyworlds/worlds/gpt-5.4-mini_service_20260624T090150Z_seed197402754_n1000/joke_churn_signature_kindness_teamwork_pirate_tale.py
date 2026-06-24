#!/usr/bin/env python3
"""
Pirate Tale storyworld: a small classical simulation about a crew aboard a ship,
where a joke can turn rough waters into kindness and teamwork, and a signature
can settle who gets the final say.

Seed tale:
---
A young pirate named Poppy loved telling jokes on the deck. One windy morning,
the crew found that the galley churned like a stormy pot, and the cook could not
finish the day's plan. Poppy's captain wanted a signature on the new route, but
the first mate worried the mood was too sour for that.

Poppy told a funny joke, and the crew started laughing. The laughter softened
the squabble. Then everyone worked together to steady the churn, share the
jobs, and sign the map with care. In the end, kindness and teamwork made the
ship feel light again.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain", "mate"}
        male = {"boy", "man", "father", "pirate", "cook"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tale:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectPrize:
    label: str
    phrase: str
    region: str
    singular: bool = True


@dataclass
class Remedy:
    id: str
    label: str
    offer: str
    action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _rush(world: World) -> list[str]:
    out: list[str] = []
    crew = world.facts["crew"]
    tale = world.facts["tale"]
    for actor in crew:
        if actor.meters.get(tale.mess, 0.0) < THRESHOLD:
            continue
        if ("rush", actor.id) in world.fired:
            continue
        world.fired.add(("rush", actor.id))
        actor.memes["trouble"] = actor.memes.get("trouble", 0.0) + 1
        out.append(f"The {tale.mess} kept the deck in a rough churn.")
    return out


def _kindness(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("kindness_done"):
        return out
    if world.facts["joke_told"] and world.facts["teamwork_started"]:
        world.facts["kindness_done"] = True
        out.append("The crew's kindness made room for a calmer plan.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rush, _kindness):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose_remedy(tale: Tale, prize: ObjectPrize) -> Optional[Remedy]:
    if tale.id == "joke" and prize.region == "heart":
        return Remedy("kind_words", "kind words", "speak kindly", "soften")
    if tale.id in {"churn", "signature"}:
        return Remedy("teamwork", "teamwork", "work together", "steady")
    return None


def predict(world: World, actor: Entity, tale: Tale, prize_id: str) -> dict:
    sim = world.copy()
    _do_act(sim, sim.get(actor.id), tale, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters.get("tangled", 0.0) >= THRESHOLD,
            "trouble": actor.memes.get("trouble", 0.0)}


def _do_act(world: World, actor: Entity, tale: Tale, narrate: bool = True) -> None:
    if tale.id not in world.setting.affords:
        return
    actor.meters[tale.mess] = actor.meters.get(tale.mess, 0.0) + 1
    actor.memes["energy"] = actor.memes.get("energy", 0.0) + 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "ship": Setting(place="the ship", affords={"joke", "churn", "signature"}),
    "harbor": Setting(place="the harbor", affords={"joke", "signature"}),
    "galley": Setting(place="the galley", affords={"churn", "joke"}),
}

TALES = {
    "joke": Tale(
        id="joke",
        verb="tell a joke",
        gerund="telling jokes",
        mess="laughs",
        soil="too loud",
        tags={"joke", "kindness"},
    ),
    "churn": Tale(
        id="churn",
        verb="stir the churn",
        gerund="churning the pot",
        mess="swirl",
        soil="all tangled",
        tags={"churn", "teamwork"},
    ),
    "signature": Tale(
        id="signature",
        verb="ask for a signature",
        gerund="signing the map",
        mess="worry",
        soil="scratched",
        tags={"signature", "teamwork"},
    ),
}

PRIZES = {
    "map": ObjectPrize("map", "the captain's route map", "hands"),
    "banner": ObjectPrize("banner", "the ship's bright banner", "mast"),
    "heart": ObjectPrize("heart", "the crew's mood", "heart"),
}

REMEDIES = [
    Remedy("kind_words", "kind words", "share kind words", "soften"),
    Remedy("teamwork", "teamwork", "work together", "steady"),
]

NAMES = ["Poppy", "Jasper", "Nina", "Milo", "Tess", "Bram", "Ivy", "Finn"]


@dataclass
class StoryParams:
    place: str
    tale: str
    prize: str
    name: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TALES.items():
        lines.append(asp.fact("tale", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r.id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Tale, Prize) :- affords(Place, Tale), setting(Place), tale(Tale), prize(Prize).
needs_teamwork(Tale) :- tale(Tale), (Tale = churn; Tale = signature).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about joke, churn, signature, kindness, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--prize", choices=PRIZES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for tale in s.affords:
            for prize in PRIZES:
                out.append((place, tale, prize))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.tale is None or c[1] == args.tale)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate tale matches the given options.)")
    place, tale, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, tale=tale, prize=prize, name=name)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(params.name, kind="character", type="pirate", label=params.name, traits=["brave", "kind"]))
    captain = world.add(Entity("Captain", kind="character", type="captain", label="the captain"))
    mate = world.add(Entity("Mate", kind="character", type="mate", label="the first mate"))
    cook = world.add(Entity("Cook", kind="character", type="cook", label="the cook"))
    prize = world.add(Entity("Prize", type=PRIZES[params.prize].label, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    world.facts.update(hero=hero, captain=captain, mate=mate, cook=cook, prize=prize, tale=TALES[params.tale], crew=[hero, captain, mate, cook])

    world.say(f"{hero.id} was a little pirate who loved {TALES[params.tale].gerund} aboard {world.setting.place}.")
    world.say(f"{hero.id} also cared a lot about kindness, because a kind crew sailed better together.")
    world.para()
    world.say(f"One windy morning on {world.setting.place}, the air felt sharp and the deck began to churn.")
    world.say(f"The {prize.type if prize.type else 'prize'} of the day was {prize.phrase}, and {captain.label} wanted a signature before the ship changed course.")
    world.say(f"But {mate.label} frowned, because the churn made everyone cross and slow.")
    world.para()

    tale = TALES[params.tale]
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    if tale.id == "joke":
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        world.say(f"{hero.id} told a joke so quick and silly that even the grumpy gulls seemed to laugh.")
        world.facts["joke_told"] = True
        world.facts["teamwork_started"] = False
    elif tale.id == "churn":
        hero.meters["swirl"] = hero.meters.get("swirl", 0.0) + 1
        world.say(f"{hero.id} reached for the spoon and helped stir the churn until it was less wild.")
        world.facts["joke_told"] = False
        world.facts["teamwork_started"] = True
    else:
        world.say(f"{hero.id} asked for a signature, but first the crew had to calm the churn and settle the mood.")
        world.facts["joke_told"] = False
        world.facts["teamwork_started"] = True

    world.para()
    world.say(f"Then {hero.id} called for teamwork, and every pirate took one small job.")
    world.say(f"The cook held the pot, the mate steadied the map, and the captain listened with a kinder face.")
    world.facts["teamwork_started"] = True
    propagate(world)
    world.say(f"At last, the crew signed the map together, and {hero.id}'s {tale.id} had turned the rough day gentle.")
    world.say("Kindness and teamwork left the ship feeling bright and steady again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate story for a young child that includes a joke, churn, and signature.',
        f"Tell a pirate tale where {f['hero'].id} helps the crew with {f['tale'].verb} and the day ends with kindness and teamwork.",
        f"Write a simple ship story where a {f['tale'].id} problem becomes better after the crew works together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    tale = f["tale"]
    prize = f["prize"]
    qa = [
        QAItem(
            question=f"Who is the story about on the ship?",
            answer=f"The story is about {hero.id}, a little pirate who cared about kindness and teamwork.",
        ),
        QAItem(
            question=f"What was the problem on the ship?",
            answer=f"The ship's {tale.mess} made the day rough, and the crew needed to calm things down before signing the map.",
        ),
        QAItem(
            question=f"What did {hero.id} do that helped the crew?",
            answer=f"{hero.id} used {tale.gerund} to help the crew, and then everyone worked together to finish the job.",
        ),
        QAItem(
            question=f"What was signed at the end?",
            answer=f"The crew signed the map, including the route plan for the ship.",
        ),
        QAItem(
            question=f"How did the mood change by the end?",
            answer="The mood changed from sour and noisy to kind, calm, and full of teamwork.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share jobs and help each other finish something together.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
        QAItem(
            question="What is a signature?",
            answer="A signature is a person's written name, often used to show agreement or approval.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="ship", tale="joke", prize="map", name="Poppy"),
    StoryParams(place="galley", tale="churn", prize="heart", name="Tess"),
    StoryParams(place="harbor", tale="signature", prize="banner", name="Ivy"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


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
        for row in combos:
            print("  ", row)
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
            header = f"### {p.name}: {p.tale} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
