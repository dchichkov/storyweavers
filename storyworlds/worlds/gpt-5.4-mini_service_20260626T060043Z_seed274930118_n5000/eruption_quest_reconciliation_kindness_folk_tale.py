#!/usr/bin/env python3
"""
A standalone storyworld for a folk-tale about an eruption, a quest, and a kind
reconciliation guided by kindness.

The world is small and classical:
- a village near a mountain
- a possible eruption that threatens a cherished bell or spring
- a quest to fetch a needed object from a cave or shrine
- a misunderstanding between two neighbors or kin
- a reconciliation achieved through kindness, not force

This script follows the Storyweavers contract:
- self-contained stdlib storyworld script
- eager import of shared results containers
- lazy ASP import inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    carried_by: Optional[str] = None
    kept_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "aunt"}
        male = {"boy", "man", "father", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    near_mountain: bool = False
    has_cave: bool = False
    has_shrine: bool = False


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    found_at: str
    useful_for: str
    plural: bool = False


@dataclass
class Challenge:
    id: str
    label: str
    danger: str
    quest_goal: str
    soot: str
    warning: str
    keyword: str = "eruption"
    tags: set[str] = field(default_factory=set)


@dataclass
class ReconciliationPath:
    id: str
    gift: str
    offer: str
    tail: str
    kindness_action: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.active_challenge: Optional[Challenge] = None
        self.quest_item: Optional[QuestItem] = None
        self.resolve_path: Optional[ReconciliationPath] = None

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.active_challenge = self.active_challenge
        clone.quest_item = self.quest_item
        clone.resolve_path = self.resolve_path
        return clone


QUESTS = {
    "bell": QuestItem(
        id="bell",
        label="village bell",
        phrase="the old village bell",
        found_at="shrine",
        useful_for="call the villagers home",
    ),
    "lantern": QuestItem(
        id="lantern",
        label="lantern",
        phrase="a bright lantern of river glass",
        found_at="cave",
        useful_for="lead the path at dusk",
    ),
    "springstone": QuestItem(
        id="springstone",
        label="springstone",
        phrase="a round springstone",
        found_at="cave",
        useful_for="keep the spring clear",
    ),
}

CHALLENGES = {
    "eruption": Challenge(
        id="eruption",
        label="eruption",
        danger="ash and glowing stones",
        quest_goal="bring back the needed thing",
        soot="gray with ash",
        warning="the mountain is waking",
        keyword="eruption",
        tags={"eruption", "mountain", "ash"},
    ),
}

PLACES = {
    "village": Place(id="village", label="the village", near_mountain=True, has_cave=False, has_shrine=True),
    "hillside": Place(id="hillside", label="the hillside village", near_mountain=True, has_cave=True, has_shrine=False),
    "valley": Place(id="valley", label="the valley hamlet", near_mountain=False, has_cave=True, has_shrine=True),
}

PATHS = {
    "kindness": ReconciliationPath(
        id="kindness",
        gift="a basket of bread and berries",
        offer="brought bread and berries to share",
        tail="shared the bread and sat together until the fear left their faces",
        kindness_action="shared food and spoke gently",
    ),
    "water": ReconciliationPath(
        id="water",
        gift="a cup of cool spring water",
        offer="brought cool spring water to share",
        tail="drank the water and let their words soften",
        kindness_action="shared water and listened well",
    ),
    "cloak": ReconciliationPath(
        id="cloak",
        gift="a warm woven cloak",
        offer="brought a warm woven cloak to share",
        tail="wrapped the cloak around the shivering child and smiled",
        kindness_action="shared warmth and listened well",
    ),
}

HERO_NAMES = ["Mara", "Tobin", "Ivo", "Anya", "Sela", "Bram", "Nina", "Perrin"]
KINSHIP = ["sister", "brother", "friend", "neighbor", "cousin"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    quest_item: str
    hero_name: str
    rival_name: str
    hero_type: str
    rival_type: str
    kinship: str
    path: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for chal_id, chal in CHALLENGES.items():
            for item_id, item in QUESTS.items():
                if place.near_mountain and item.found_at in {"cave", "shrine"}:
                    for path_id in PATHS:
                        out.append((place_id, chal_id, item_id, path_id))
    return out


def reasonableness_gate(place: Place, challenge: Challenge, item: QuestItem, path: ReconciliationPath) -> bool:
    return place.near_mountain and item.found_at in {"cave", "shrine"} and path.kindness_action


ASP_RULES = r"""
near_mountain(village). near_mountain(hillside). not near_mountain(valley) :- valley.
found_at(bell,shrine). found_at(lantern,cave). found_at(springstone,cave).

valid(P,C,I,Path) :- near_mountain(P), found_at(I,_), challenge(C), path(Path).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.near_mountain:
            lines.append(asp.fact("near_mountain", pid))
        if place.has_cave:
            lines.append(asp.fact("has_cave", pid))
        if place.has_shrine:
            lines.append(asp.fact("has_shrine", pid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for iid, item in QUESTS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("found_at", iid, item.found_at))
    for pid in PATHS:
        lines.append(asp.fact("path", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld of eruption, quest, reconciliation, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--quest-item", choices=QUESTS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--hero-name")
    ap.add_argument("--rival-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--rival-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--kinship", choices=KINSHIP)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.quest_item is None or c[2] == args.quest_item)
              and (args.path is None or c[3] == args.path)]
    if not combos:
        raise StoryError("No valid story combination matches the given options.")
    place, challenge, item, path = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy", "woman", "man"])
    rival_type = args.rival_type or rng.choice([t for t in ["girl", "boy", "woman", "man"] if t != hero_type])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    rival_name = args.rival_name or rng.choice([n for n in HERO_NAMES if n != hero_name])
    kinship = args.kinship or rng.choice(KINSHIP)
    return StoryParams(place=place, challenge=challenge, quest_item=item, hero_name=hero_name,
                       rival_name=rival_name, hero_type=hero_type, rival_type=rival_type,
                       kinship=kinship, path=path)


def _introduce(world: World, hero: Entity, rival: Entity, kinship: str) -> None:
    world.say(f"Long ago, in {world.place.label}, there lived {hero.pronoun('possessive')} {kinship}, {rival.id}.")
    world.say(f"{hero.id} was a kind {hero.type} who noticed small troubles before they became large ones.")
    world.say(f"{rival.id} was quick to fret when the mountain rumbled, for folk tales had taught {rival.pronoun('object')} to listen.")


def _quest(world: World, hero: Entity, rival: Entity, item: QuestItem, chal: Challenge) -> None:
    hero.memes["duty"] = hero.memes.get("duty", 0.0) + 1
    world.say(f"When the mountain gave a low growl, the elder said the village must {chal.quest_goal}.")
    world.say(f"So {hero.id} set out to find {item.phrase}.")
    if item.found_at == "cave":
        world.say("The cave mouth yawned beneath hanging vines, cool and dark as a closed eye.")
    else:
        world.say("The shrine stood on a stony rise, and its candles trembled in the draft.")
    hero.meters["journey"] = hero.meters.get("journey", 0.0) + 1
    hero.meters["courage"] = hero.meters.get("courage", 0.0) + 1
    world.say(f"{hero.id} carried {item.label} home because the village needed it most.")


def _conflict(world: World, hero: Entity, rival: Entity, chal: Challenge, item: QuestItem) -> None:
    rival.memes["fear"] = rival.memes.get("fear", 0.0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    world.para()
    world.say(f"But {rival.id} had earlier hidden the path marker in a fit of worry.")
    world.say(f"{hero.id} found it again, and {rival.id} thought {hero.id} was being harsh.")
    world.say(f"That made the little quarrel sting just as the mountain began to smoke.")
    world.say(f"Above them the {chal.keyword} warning grew true: ash drifted like gray snow over the roofs.")


def _reconcile(world: World, hero: Entity, rival: Entity, path: ReconciliationPath, item: QuestItem) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    rival.memes["kindness"] = rival.memes.get("kindness", 0.0) + 1
    rival.memes["fear"] = 0.0
    hero.memes["hurt"] = 0.0
    world.para()
    world.say(f"Then {hero.id} chose kindness over pride.")
    world.say(f"{hero.id} {path.offer}, and asked {rival.id} to sit close and breathe with {hero.id}.")
    world.say(f"{rival.id} blinked away tears, for the gentle offer felt like a hand held out in the dark.")
    world.say(f"Together they {path.tail}.")
    world.say(f"When the bell rang and the ash fell, the village stayed calm because the two of them stood together.")


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    challenge = CHALLENGES[params.challenge]
    item = QUESTS[params.quest_item]
    path = PATHS[params.path]
    world = World(place)
    world.active_challenge = challenge
    world.quest_item = item
    world.resolve_path = path

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    rival = world.add(Entity(id=params.rival_name, kind="character", type=params.rival_type))

    _introduce(world, hero, rival, params.kinship)
    _quest(world, hero, rival, item, challenge)
    _conflict(world, hero, rival, challenge, item)
    _reconcile(world, hero, rival, path, item)

    world.facts.update(hero=hero, rival=rival, place=place, challenge=challenge, item=item, path=path, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale about an eruption near {f['place'].label} that sends {f['hero'].id} on a quest.",
        f"Tell a gentle story where {f['hero'].id} and {f['rival'].id} quarrel, then reconcile through kindness.",
        f"Make a simple story about {f['item'].phrase}, a mountain rumble, and a happy ending for the village.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    item = f["item"]
    place = f["place"]
    chal = f["challenge"]
    path = f["path"]
    return [
        QAItem(
            question=f"Who went on the quest when the mountain began its eruption warning?",
            answer=f"{hero.id} went on the quest for {item.phrase} so the village could be safe.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {rival.id} have a quarrel in the story?",
            answer=f"They quarreled because {rival.id} had hidden the path marker and thought {hero.id} was being too harsh when it was found again.",
        ),
        QAItem(
            question=f"How did the story end after the eruption fear and the quarrel?",
            answer=f"It ended with kindness: {hero.id} {path.offer}, and the two of them sat together until the fear left their faces.",
        ),
        QAItem(
            question=f"What did {item.label} help the village do?",
            answer=f"{item.phrase} helped the villagers {item.useful_for}.",
        ),
        QAItem(
            question=f"What kind of danger did the mountain bring to {place.label}?",
            answer=f"The mountain brought {chal.danger}, which made everyone hurry and listen carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an eruption?",
            answer="An eruption is when a volcano or mountain sends out hot lava, ash, and stones from inside the ground.",
        ),
        QAItem(
            question="What is a quest in a folk tale?",
            answer="A quest is a journey to find something important or to help someone in need.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place: {world.place.label}")
    if world.active_challenge:
        lines.append(f"challenge: {world.active_challenge.id}")
    if world.quest_item:
        lines.append(f"quest_item: {world.quest_item.label}")
    if world.resolve_path:
        lines.append(f"reconciliation: {world.resolve_path.id}")
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


def explain_rejection(place: Place, item: QuestItem) -> str:
    return f"(No story: {item.label} does not fit this mountain quest in {place.label}.)"


CURATED = [
    StoryParams(place="village", challenge="eruption", quest_item="bell", hero_name="Mara", rival_name="Tobin",
                hero_type="girl", rival_type="boy", kinship="brother", path="kindness"),
    StoryParams(place="hillside", challenge="eruption", quest_item="lantern", hero_name="Anya", rival_name="Bram",
                hero_type="woman", rival_type="man", kinship="neighbor", path="water"),
    StoryParams(place="valley", challenge="eruption", quest_item="springstone", hero_name="Sela", rival_name="Nina",
                hero_type="girl", rival_type="girl", kinship="cousin", path="cloak"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_random_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.quest_item is None or c[2] == args.quest_item)
              and (args.path is None or c[3] == args.path)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, chal, item, path = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        challenge=chal,
        quest_item=item,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        rival_name=args.rival_name or rng.choice([n for n in HERO_NAMES if n != (args.hero_name or "")]),
        hero_type=args.hero_type or rng.choice(["girl", "boy", "woman", "man"]),
        rival_type=args.rival_type or rng.choice(["girl", "boy", "woman", "man"]),
        kinship=args.kinship or rng.choice(KINSHIP),
        path=path,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible story combinations:")
        for combo in combos:
            print("  ", combo)
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
            params = build_random_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.challenge} at {p.place} (quest: {p.quest_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
