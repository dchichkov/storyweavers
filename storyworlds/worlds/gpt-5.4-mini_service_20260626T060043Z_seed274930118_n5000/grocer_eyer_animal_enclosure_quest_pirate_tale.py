#!/usr/bin/env python3
"""
A standalone storyworld for a pirate-flavored quest in an animal enclosure.

Seed premise:
- A grocer and an eyer have a quest.
- The setting is an animal enclosure.
- The style should feel like a small pirate tale: shipshape talk, a map, a clue,
  a tense turn, and a cheerful payoff.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

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
    place: str = "the animal enclosure"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    clue: str
    seek_verb: str
    danger: str
    risk: str
    zone: set[str]
    keyword: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet", "muddy"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and dirty.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("defiance", 0.0) < THRESHOLD or actor.memes.get("held_back", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soak, _r_work, _r_conflict):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the animal enclosure", indoors=False, affords={"quest", "sneak", "spot"})
QUESTS = {
    "coinquest": Quest(
        id="coinquest",
        title="find the lost captain's coin",
        clue="a shiny clue by the fox den",
        seek_verb="find the lost coin",
        danger="the muddy path by the otter pool",
        risk="muddy and wet",
        zone={"feet", "legs"},
        keyword="coin",
        tags={"coin", "quest", "pirate"},
    ),
    "featherquest": Quest(
        id="featherquest",
        title="find the bright parrot feather",
        clue="a bright feather stuck in a low fence",
        seek_verb="find the feather",
        danger="the splashy pond rail",
        risk="wet",
        zone={"feet", "legs"},
        keyword="feather",
        tags={"feather", "quest", "pirate"},
    ),
}
PRIZES = {
    "boots": Prize(label="boots", phrase="spry sailing boots", type="boots", region="feet", plural=True),
    "cloak": Prize(label="cloak", phrase="a red pirate cloak", type="cloak", region="torso"),
    "satchel": Prize(label="satchel", phrase="a stitched map satchel", type="satchel", region="torso"),
}
GEAR = [
    Gear(id="mudboots", label="mud boots", covers={"feet"}, guards={"muddy", "wet"}, prep="pull on mud boots first", tail="stepped back for the mud boots", plural=True),
    Gear(id="cloakwrap", label="a waxed cloak", covers={"torso"}, guards={"wet"}, prep="wrap a waxed cloak around the chest", tail="wrapped up the waxed cloak"),
    Gear(id="trailers", label="trail shoes", covers={"feet"}, guards={"wet", "muddy"}, prep="lace up trail shoes", tail="laced up the trail shoes", plural=True),
}
GROCER_NAMES = ["Gwen", "Mira", "Lena", "Nell", "Pip"]
EYER_NAMES = ["Ivo", "Ezra", "Jory", "Tess", "Ari"]


@dataclass
class StoryParams:
    quest: str
    prize: str
    grocer_name: str
    eyer_name: str
    seed: Optional[int] = None


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and any(m in gear.guards for m in ("wet", "muddy")):
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for qid, q in QUESTS.items():
        for pid, p in PRIZES.items():
            if quest_at_risk(q, p) and select_gear(q, p):
                out.append((SETTING.place, qid, pid))
    return out


def tell(quest: Quest, prize_cfg: Prize, grocer_name: str, eyer_name: str) -> World:
    world = World(SETTING)
    grocer = world.add(Entity(id=grocer_name, kind="character", type="grocer", label="the grocer", meters={}, memes={}))
    eyer = world.add(Entity(id=eyer_name, kind="character", type="eyer", label="the eyer", meters={}, memes={}))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=grocer.id, caretaker=eyer.id, region=prize_cfg.region, plural=prize_cfg.plural))

    grocer.memes["love_quest"] = 1
    eyer.memes["love_quest"] = 1

    world.say(f"{grocer_name} was a grocer with a salt-bright smile, and {eyer_name} was an eyer who could spot a tiny clue from far away.")
    world.say(f"They had a pirate quest in the animal enclosure: to {quest.seek_verb}.")
    world.say(f"On a windy morning, they carried a little map, and the map pointed toward {quest.clue}.")
    world.say(f"{grocer_name} wore {prize.phrase} and kept looking toward the {quest.keyword} trail like a hopeful little captain.")

    world.para()
    world.zone = set(quest.zone)
    world.say(f"At the animal enclosure, they reached the {quest.danger}, where the ground looked {quest.risk}.")
    world.say(f"{eyer_name} spotted the clue first, but {grocer_name} wanted to hurry and {quest.seek_verb} right away.")
    grocer.meters["wet"] = grocer.meters.get("wet", 0.0) + 1
    propagate(world)
    world.say(f"{grocer_name} frowned when the path splashed up at the {prize.label}.")
    grocer.memes["defiance"] = 1
    eyer.memes["held_back"] = 1
    propagate(world)
    world.say(f"{eyer_name} lifted a hand and said, 'Hold, matey. That path will ruin the {prize.label}.'")
    world.say(f"{grocer_name} stamped one boot in the mud, then listened.")

    world.para()
    gear = select_gear(quest, prize)
    if gear is None:
        raise StoryError("No safe pirate fix fits this quest and prize.")
    if gear.id == "mudboots":
        world.say(f"{eyer_name} smiled and fetched mud boots from a neat crate by the gate.")
    elif gear.id == "cloakwrap":
        world.say(f"{eyer_name} found a waxed cloak hanging beside the keeper's bench.")
    else:
        world.say(f"{eyer_name} picked trail shoes from the supply chest.")
    item = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    item.worn_by = grocer.id
    world.say(f"{grocer_name} tried on {gear.label}, and the fit felt shipshape.")
    world.say(f"Then they went back along the clue, and {gear.tail}.")
    grocer.memes["joy"] = grocer.memes.get("joy", 0.0) + 1
    grocer.memes["conflict"] = 0
    world.say(f"Together they {quest.seek_verb}, and at last they found the little prize hidden beside the fox den.")
    world.say(f"{grocer_name} laughed, {eyer_name} grinned, and the animal enclosure felt like a treasure island made of grass and sunlight.")

    world.facts.update(grocer=grocer, eyer=eyer, prize=prize, quest=quest, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child about a grocer named {f["grocer"].id} and an eyer named {f["eyer"].id} who have a quest in an animal enclosure.',
        f"Tell a gentle quest story where {f['grocer'].id} wants to {f['quest'].seek_verb} but the path near the animal enclosure is too {f['quest'].risk}, so {f['eyer'].id} helps with a safe fix.",
        f'Write a simple pirate-style story that includes a clue, a map, and the word "{f["quest"].keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    grocer = f["grocer"]
    eyer = f["eyer"]
    quest = f["quest"]
    prize = f["prize"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who went on the pirate quest in the animal enclosure?",
            answer=f"{grocer.id} the grocer and {eyer.id} the eyer went on the quest together.",
        ),
        QAItem(
            question=f"What did they want to do on their quest?",
            answer=f"They wanted to {quest.seek_verb}.",
        ),
        QAItem(
            question=f"Why did {eyer.id} slow {grocer.id} down near {quest.danger}?",
            answer=f"Because the path was {quest.risk}, and that could have ruined the {prize.label} that {grocer.id} was wearing.",
        ),
        QAItem(
            question=f"What helped {grocer.id} keep going without getting the {prize.label} ruined?",
            answer=f"{gear.label} helped {grocer.id} stay safe on the damp path while they kept chasing the clue.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"They found the hidden prize, and the two friends finished the quest smiling in the animal enclosure.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to find something important or to reach a goal.",
        )
    ],
    "pirate": [
        QAItem(
            question="What is pirate talk like?",
            answer="Pirate talk often sounds playful and bold, with words like matey, ahoy, and treasure.",
        )
    ],
    "coin": [
        QAItem(
            question="What is a coin?",
            answer="A coin is a small flat piece of metal that people use as money.",
        )
    ],
    "feather": [
        QAItem(
            question="What is a feather?",
            answer="A feather is the soft covering on a bird, and it can be light and colorful.",
        )
    ],
    "wet": [
        QAItem(
            question="What does wet mean?",
            answer="Wet means covered with water or damp from water.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    out: list[QAItem] = []
    for tag in ("quest", "pirate", "coin", "feather", "wet"):
        if tag in tags or tag == "quest" or tag == "pirate":
            out.extend(WORLD_KNOWLEDGE.get(tag, []))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_at_risk(Q,P) :- quest(Q), prize(P), zone(Q,R), worn_on(P,R).
safe_fix(Q,P) :- quest_at_risk(Q,P), gear(G), covers(G,R), worn_on(P,R), guards(G,mud).
valid_story(S,Q,P) :- setting(S), affords(S,quest), quest_at_risk(Q,P), safe_fix(Q,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "animal_enclosure"))
    lines.append(asp.fact("affords", "animal_enclosure", "quest"))
    lines.append(asp.fact("affords", "animal_enclosure", "sneak"))
    lines.append(asp.fact("affords", "animal_enclosure", "spot"))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for r in sorted(q.zone):
            lines.append(asp.fact("zone", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
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
    ap = argparse.ArgumentParser(description="Pirate-tale quest in an animal enclosure.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--grocer-name", choices=GROCER_NAMES)
    ap.add_argument("--eyer-name", choices=EYER_NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if args.quest and args.prize:
        if not (quest_at_risk(QUESTS[args.quest], PRIZES[args.prize]) and select_gear(QUESTS[args.quest], PRIZES[args.prize])):
            raise StoryError("No valid quest/prize pair matches the requested options.")
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, qid, pid = rng.choice(sorted(combos))
    grocer_name = args.grocer_name or rng.choice(GROCER_NAMES)
    eyer_name = args.eyer_name or rng.choice(EYER_NAMES)
    return StoryParams(quest=qid, prize=pid, grocer_name=grocer_name, eyer_name=eyer_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(QUESTS[params.quest], PRIZES[params.prize], params.grocer_name, params.eyer_name)
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
    StoryParams(quest="coinquest", prize="boots", grocer_name="Gwen", eyer_name="Ivo"),
    StoryParams(quest="featherquest", prize="cloak", grocer_name="Mira", eyer_name="Tess"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            header = f"### {p.grocer_name} and {p.eyer_name}: {p.quest} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
