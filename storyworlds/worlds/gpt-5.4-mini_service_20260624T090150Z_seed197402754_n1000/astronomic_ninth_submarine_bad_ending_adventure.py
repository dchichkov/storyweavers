#!/usr/bin/env python3
"""
A small adventure storyworld about an astronomic submarine mission with a bad ending.

This world is intentionally narrow: it models one brave child-scale expedition
in which a ninth dive goes wrong, the crew tries to reach a star chart, and the
ending proves what changed. The bad ending is safe for children, but it leaves a
sense of loss and a quiet finish instead of a happy fix.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    depth: str
    wonders: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    danger: str
    risk: str
    place: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CrewAid:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


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


@dataclass
class StoryParams:
    setting: str
    artifact: str
    aid: str
    name: str
    gender: str
    captain: str
    seed: Optional[int] = None


SETTINGS = {
    "abyss": Setting(place="the deep blue abyss", depth="far below the waves", wonders={"stars", "coral"}),
    "trench": Setting(place="the quiet trench", depth="down where the water felt heavy", wonders={"stars", "shells"}),
}

ARTIFACTS = {
    "chart": Artifact(
        id="chart",
        label="astronomic chart",
        phrase="an astronomic chart with a ninth star circled in gold",
        danger="lost",
        risk="could drift away in the dark water",
        place="the chart room",
        keyword="astronomic",
        tags={"astronomic", "ninth", "stars"},
    ),
    "lens": Artifact(
        id="lens",
        label="astronomic lens",
        phrase="an astronomic lens that could catch the tiniest star-light",
        danger="cracked",
        risk="could fog up and turn useless",
        place="the little observatory bay",
        keyword="astronomic",
        tags={"astronomic", "stars"},
    ),
}

AIDS = {
    "hulllight": CrewAid(
        id="hulllight",
        label="hull lantern",
        prep="switch on the hull lantern and tie the chart to the rail",
        tail="switched on the hull lantern and tied the chart to the rail",
        guards={"lost"},
    ),
    "case": CrewAid(
        id="case",
        label="sealed case",
        prep="slide the lens into a sealed case first",
        tail="slid the lens into a sealed case first",
        guards={"cracked", "fogged"},
    ),
}

NAMES = ["Ava", "Milo", "Noah", "Mira", "Lea", "Finn", "Iris", "Theo"]
GENDERS = {"girl": ["Ava", "Mira", "Lea", "Iris"], "boy": ["Milo", "Noah", "Finn", "Theo"]}
CAPTAINS = ["captain", "pilot", "guide", "older sister", "older brother"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ARTIFACTS:
            for aid in AIDS:
                combos.append((s, a, aid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.artifact and args.artifact not in ARTIFACTS:
        raise StoryError("Unknown artifact.")
    if args.aid and args.aid not in AIDS:
        raise StoryError("Unknown crew aid.")

    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.artifact:
        combos = [c for c in combos if c[1] == args.artifact]
    if args.aid:
        combos = [c for c in combos if c[2] == args.aid]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, artifact, aid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDERS[gender])
    captain = args.captain or rng.choice(CAPTAINS)
    return StoryParams(setting=setting, artifact=artifact, aid=aid, name=name, gender=gender, captain=captain)


def prize_at_risk(artifact: Artifact) -> bool:
    return True


def select_aid(artifact: Artifact) -> Optional[CrewAid]:
    aid = AIDS[artifact.id == "chart" and "hulllight" or "case"]
    if artifact.id == "chart" and "lost" in aid.guards:
        return aid
    if artifact.id == "lens" and "cracked" in aid.guards:
        return aid
    return None


def predict_bad_end(world: World, hero: Entity, artifact: Artifact) -> dict:
    sim = world.copy()
    _begin_mission(sim, sim.get(hero.id), artifact, narrate=False)
    lost = sim.facts.get("bad_end", False)
    return {"bad_end": lost}


def _begin_mission(world: World, hero: Entity, artifact: Artifact, narrate: bool = True) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.meters["hope"] = hero.meters.get("hope", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} boarded the submarine with a bright smile and a brave little pack.")
        world.say(f"Down {world.setting.depth}, they were looking for {artifact.phrase}.")


def tell(setting: Setting, artifact: Artifact, aid: CrewAid, hero_name: str, hero_type: str, captain: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    boss = world.add(Entity(id="CrewLead", kind="character", type="adult", label=captain))
    item = world.add(Entity(id=artifact.id, type="artifact", label=artifact.label, phrase=artifact.phrase, owner=hero.id))
    world.facts.update(hero=hero, boss=boss, artifact=item, aid=aid, setting=setting)

    world.say(f"{hero.id} was a small {hero.type} who loved adventure and bright ideas.")
    world.say(f"{hero.id} especially loved astronomic things, like maps of stars and stories about the ninth star.")
    world.say(f"One day, {hero.id} climbed into a tiny submarine with {boss.label} for a careful trip under the sea.")

    world.para()
    world.say(f"Deep below the water, the submarine hummed softly in {setting.place}.")
    world.say(f"They searched for {artifact.phrase}, because the crew hoped to bring it home safely.")

    world.para()
    world.say(f"{hero.id} wanted to {artifact.keyword} the mission right away, but {boss.label} pointed to the danger.")
    world.say(f'"If we rush, {artifact.risk}," {boss.label} said.')
    world.say(f"{hero.id} still reached for the {artifact.label} and wished the dark water would move aside.")

    world.para()
    aid_used = select_aid(artifact)
    if aid_used is not None:
        world.say(f"Then {boss.label} offered a careful plan: {aid_used.prep}.")
        world.say(f"{hero.id} nodded, and for a moment the little submarine felt safe and clever.")
    world.say(f"But the sea had its own idea.")
    world.say(f"A cold wobble shook the hull, and the light blinked twice.")
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.meters["lost"] = hero.meters.get("lost", 0.0) + 1
    world.facts["bad_end"] = True

    world.para()
    if artifact.id == "chart":
        world.say(f"The astronomic chart slipped from its clip and spun into a dark corner nobody could reach.")
        world.say(f"{hero.id} pressed a hand to the glass, but the ninth star disappeared into the black water.")
        world.say(f"The crew went home with an empty holder where the chart had been.")
    else:
        world.say(f"The astronomic lens misted over, and the last bright dot turned fuzzy and far away.")
        world.say(f"{hero.id} wiped the glass again and again, but the tiny star-light would not come back.")
        world.say(f"The crew turned the submarine around, carrying a silent empty frame instead of a shining prize.")

    hero.memes["sadness"] = hero.memes.get("sadness", 0.0) + 1
    boss.memes["regret"] = boss.memes.get("regret", 0.0) + 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    art = f["artifact"]
    return [
        f'Write an adventure story for a young child about {hero.id} in a submarine, with the word "astronomic".',
        f"Tell a short adventure where a {hero.type} named {hero.id} chases {art.phrase} in a submarine, but the ending is sad.",
        f"Write a simple submarine adventure featuring the ninth star and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    boss = f["boss"]
    art = f["artifact"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who went on the submarine adventure?",
            answer=f"It was about {hero.id}, a small {hero.type}, and {boss.label}, who guided the trip.",
        ),
        QAItem(
            question=f"What were they searching for under the sea?",
            answer=f"They were searching for {art.phrase} in {world.setting.place}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: the {art.label} was lost or failed to help, and the crew came home disappointed.",
        ),
        QAItem(
            question=f"How did the helper plan try to keep things safe?",
            answer=f"They tried to use the {aid.label} by {aid.prep}, so the mission could stay careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a submarine?",
            answer="A submarine is a boat that can travel underwater.",
        ),
        QAItem(
            question="What does astronomic mean?",
            answer="Astronomic means it has to do with stars, space, or the sky at night.",
        ),
        QAItem(
            question="What does the ninth mean?",
            answer="The ninth means number nine in a counting list.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,A,AD) :- setting(S), artifact(A), aid(AD).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ARTIFACTS:
        lines.append(asp.fact("artifact", aid))
    for x in AIDS:
        lines.append(asp.fact("aid", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: astronomic submarine mission with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=CAPTAINS)
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


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    artifact = ARTIFACTS[params.artifact]
    aid = AIDS[params.aid]
    world = tell(setting, artifact, aid, params.name, params.gender, params.captain)
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
    StoryParams(setting="abyss", artifact="chart", aid="hulllight", name="Mira", gender="girl", captain="captain"),
    StoryParams(setting="trench", artifact="lens", aid="case", name="Theo", gender="boy", captain="guide"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
