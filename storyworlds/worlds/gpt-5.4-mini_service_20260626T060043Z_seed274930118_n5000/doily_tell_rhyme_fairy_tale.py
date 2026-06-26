#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a doily, a royal telling, and a gentle
rhyme-driven turn.

Premise:
- A child or small creature loves a treasured doily.
- A storyteller or elder tells a rhyme or tale.
- The doily is at risk of getting dusty, soggy, or rumpled during a story-time
  task.
- A compatible fix exists: a careful cover, a folded place, or a special tray.

The world is intentionally small and constraint-checked so every generated story
has a clear beginning, a turn, and a soft ending image.
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    covered_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["dusty", "rumpled", "wet", "safe", "joy", "worry", "wonder", "care"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "witch", "lady"}
        male = {"boy", "father", "king", "man", "wizard", "lord"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the cottage"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Tale:
    id: str
    name: str
    rhyme: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "tell"
    tags: set[str] = field(default_factory=set)


@dataclass
class Cover:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    protective: bool = True


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def covered(self, ent: Entity, region: str) -> bool:
        return any(
            obj.protective and region in obj.covers and obj.covered_by == ent.id
            for obj in self.entities.values()
        )


@dataclass
class StoryParams:
    place: str
    tale: str
    doily: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


SETTINGS = {
    "cottage": Setting("the cottage", True, {"tell", "rhyme"}),
    "hall": Setting("the candlelit hall", True, {"tell", "rhyme"}),
    "garden": Setting("the moon garden", False, {"tell", "rhyme"}),
}

TALES = {
    "moon": Tale(
        id="moon",
        name="moon tale",
        rhyme="moon and spoon",
        mess="dusty",
        soil="dusty and dull",
        zone={"table", "hands"},
        tags={"moon", "rhyme"},
    ),
    "rose": Tale(
        id="rose",
        name="rose rhyme",
        rhyme="rose and nose",
        mess="wet",
        soil="damp and sad",
        zone={"table", "hem"},
        tags={"rose", "rhyme"},
    ),
    "bread": Tale(
        id="bread",
        name="bread tale",
        rhyme="bread and bed",
        mess="rumpled",
        soil="creased and crumpled",
        zone={"lap", "hands"},
        tags={"bread", "rhyme"},
    ),
}

COVERS = [
    Cover(
        id="glass_case",
        label="a glass case",
        prep="place the doily under a glass case first",
        tail="slid the doily safely under the glass case",
        covers={"table", "hands", "hem", "lap"},
        guards={"dusty", "wet", "rumpled"},
    ),
    Cover(
        id="linen_wrap",
        label="a linen wrap",
        prep="wrap the doily in clean linen first",
        tail="wrapped the doily in clean linen",
        covers={"table", "hands", "lap"},
        guards={"dusty", "rumpled"},
    ),
    Cover(
        id="dry_tray",
        label="a dry tray",
        prep="set the doily on a dry tray first",
        tail="set the doily on the dry tray",
        covers={"table"},
        guards={"dusty", "wet"},
    ),
]

GIRL_NAMES = ["Elsie", "Mara", "Nina", "Clara", "Luna", "Pia"]
BOY_NAMES = ["Owen", "Felix", "Robin", "Theo", "Jasper", "Milo"]
ELDERS = ["grandmother", "grandfather", "aunt", "uncle", "seamstress", "bard"]
TRAITS = ["gentle", "curious", "brave", "kind", "dreamy"]


def prize_at_risk(tale: Tale) -> bool:
    return True


def select_cover(tale: Tale) -> Optional[Cover]:
    for c in COVERS:
        if tale.mess in c.guards:
            return c
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for tale_id, tale in TALES.items():
            if "tell" in setting.affords and "rhyme" in setting.affords and prize_at_risk(tale) and select_cover(tale):
                out.append((place, tale_id, "doily"))
    return out


def tell(world: World, tale: Tale, child: Entity, elder: Entity, doily: Entity) -> None:
    world.say(
        f"In {world.setting.place}, there lived a little {child.type} named {child.id} who loved a fine doily."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} liked the soft lace, and {elder.pronoun('subject')} loved to tell a {tale.name} in rhyme."
    )
    world.say(
        f"The rhyme ran like this: “{tale.rhyme}.”"
    )
    doily.memes["care"] += 1
    child.memes["joy"] += 1


def warn(world: World, elder: Entity, child: Entity, tale: Tale, doily: Entity) -> bool:
    pred = world.copy()
    perform_tale(pred, child, tale, doily, narrate=False)
    if pred.get(doily.id).meters[tale.mess] >= THRESHOLD:
        world.facts["soil"] = tale.soil
        world.say(
            f'"If we tell that tale too freely," {elder.id} said, "your doily may end up {tale.soil}."'
        )
        return True
    return False


def perform_tale(world: World, child: Entity, tale: Tale, doily: Entity, narrate: bool = True) -> None:
    world.zone = set(tale.zone)
    child.memes["wonder"] += 1
    doily.meters[tale.mess] += 1
    doily.meters["safe"] = 0.0
    if narrate:
        world.say(
            f"As the {tale.name} went on, the little doily lay near the table and could be spoiled by the {tale.mess} tale."
        )


def resolution(world: World, child: Entity, elder: Entity, tale: Tale, doily: Entity) -> None:
    cover_def = select_cover(tale)
    if not cover_def:
        raise StoryError("No gentle cover fits this tale.")
    cover = world.add(Entity(
        id=cover_def.id,
        type="thing",
        label=cover_def.label,
        protective=True,
        covers=set(cover_def.covers),
        owner=child.id,
        caretaker=elder.id,
    ))
    cover.covered_by = child.id
    if world.copy().get(doily.id).meters[tale.mess] >= THRESHOLD:
        pass
    world.say(
        f"Then {elder.id} smiled and said, “{cover_def.prep}.”"
    )
    world.say(
        f"{child.id} listened, and together they {cover_def.tail}."
    )
    world.say(
        f"So the tale could be told in peace, the doily stayed clean, and the moonlight made the lace look like frost."
    )
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    doily.meters[tale.mess] = 0.0
    doily.meters["safe"] += 1
    world.facts["cover"] = cover_def
    world.facts["resolved"] = True


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder", label=params.elder))
    doily = world.add(Entity(
        id="doily",
        type="thing",
        label="doily",
        phrase="a white lace doily",
        owner=child.id,
        caretaker=elder.id,
    ))
    tale = TALES[params.tale]
    world.facts.update(child=child, elder=elder, doily=doily, tale=tale, place=params.place)

    tell(world, tale, child, elder, doily)
    world.para()
    warn(world, elder, child, tale, doily)
    perform_tale(world, child, tale, doily)
    world.para()
    resolution(world, child, elder, tale, doily)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, elder, tale = f["child"], f["elder"], f["tale"]
    return [
        f'Write a short fairy tale about a child named {child.id}, a doily, and a tale told in rhyme.',
        f"Tell a gentle story where {elder.id} warns {child.id} that the {tale.name} could spoil the doily.",
        f'Write a simple fairy tale that includes the words "doily" and "tell" and ends with a safe, happy image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, tale, doily = f["child"], f["elder"], f["tale"], f["doily"]
    return [
        QAItem(
            question=f"Who loved the doily in the story?",
            answer=f"{child.id} loved the doily because it was soft, pretty, and special.",
        ),
        QAItem(
            question=f"What did {elder.id} tell in the cottage?",
            answer=f"{elder.id} told a {tale.name} in rhyme, and the rhyme made the room feel magical.",
        ),
        QAItem(
            question=f"Why did {elder.id} warn about the doily?",
            answer=f"{elder.id} warned that the {tale.name} could leave the doily {tale.soil} if they did not protect it.",
        ),
        QAItem(
            question=f"How did they keep the doily safe?",
            answer=f"They used a careful cover so the doily stayed clean while the tale was told.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tale = f["tale"]
    qa = [
        QAItem(
            question="What is a doily?",
            answer="A doily is a small decorative cloth, often made with lace or fine thread, used to dress up a table or shelf.",
        ),
        QAItem(
            question="What does it mean to tell a tale?",
            answer="To tell a tale means to speak or share a story aloud, often with a beginning, middle, and end.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the ends, like moon and spoon.",
        ),
    ]
    if "rhyme" in tale.tags:
        qa.append(QAItem(
            question="Why do people like rhyme in stories?",
            answer="People like rhyme because it makes stories fun to hear and easy to remember.",
        ))
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(T) :- tale(T).
has_cover(T) :- tale(T), mess_of(T,M), guards(C,M), cover(C).
valid_story(P,T) :- setting(P), affords(P,tell), affords(P,rhyme), prize_at_risk(T), has_cover(T).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TALES.items():
        lines.append(asp.fact("tale", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for c in COVERS:
        lines.append(asp.fact("cover", c.id))
        for m in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, m))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale doily storyworld with rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--doily", choices=["doily"], default="doily")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.tale:
        combos = [c for c in combos if c[1] == args.tale]
    if not combos:
        raise StoryError("No valid fairy-tale combination matches the given options.")
    place, tale_id, _ = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or "girl") == "girl" else BOY_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, tale=tale_id, doily="doily", name=name, gender=gender, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(place="cottage", tale="moon", doily="doily", name="Elsie", gender="girl", elder="grandmother"),
    StoryParams(place="hall", tale="bread", doily="doily", name="Theo", gender="boy", elder="bard"),
    StoryParams(place="garden", tale="rose", doily="doily", name="Mara", gender="girl", elder="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
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
            header = f"### {p.name}: {p.tale} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
