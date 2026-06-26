#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/scripture_quest_sharing_myth.py
=============================================================================================================

A tiny mythic storyworld about a sacred scripture, a quest, and the power of
sharing. The world stays small and classical: a keeper sets out to recover a
missing scripture, meets a test on the road, and discovers that sharing the
text changes the ending.

The premise is built from a seed-like tale:
- A temple keeps a scripture scroll in a cedar chest.
- A young keeper wants to read it aloud at the next moon rite.
- The scroll is taken or misplaced, sending the keeper on a quest.
- The keeper meets a traveler who knows part of the verse.
- Sharing the scripture with others reveals the final path home.

The simulation uses physical meters and emotional memes:
- meters track things like distance, carried items, and damage.
- memes track devotion, fear, hope, and fellowship.

The ASP twin encodes the same reasonableness gate:
- a quest is valid only when the scripture is at risk,
- a fitting helper exists,
- and the sharing move can genuinely resolve the trouble.
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
    keeper: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "priest"}
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
    affords: set[str] = field(default_factory=set)
    near: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    damage: str
    keyword: str = "scripture"
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    teaches: str
    carries: str
    resolve: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_wear_damage(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.get("keeper")
    scroll = world.get("scripture")
    if keeper.meters.get("questing", 0) < THRESHOLD:
        return out
    if scroll.meters.get("safe", 0) >= THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scroll.meters["creased"] = scroll.meters.get("creased", 0) + 1
    scroll.meters["at_risk"] = 1
    out.append("The scripture was no longer safe in the cedar chest.")
    return out


def _r_fear_to_hope(world: World) -> list[str]:
    keeper = world.get("keeper")
    if keeper.memes.get("fear", 0) < THRESHOLD:
        return []
    sig = ("hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keeper.memes["hope"] = keeper.memes.get("hope", 0) + 1
    return ["__hope__"]


CAUSAL_RULES = [
    _r_wear_damage,
    _r_fear_to_hope,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(s for s in items if s != "__hope__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(quest: Quest) -> bool:
    return "scripture" in quest.tags


def select_helper(quest: Quest, helper: Helper) -> bool:
    return quest.id in {"lost_scroll", "missing_verse"} and helper.resolve == "share"


def tell(place: Place, quest: Quest, helper: Helper,
         keeper_name: str = "Ari", keeper_type: str = "boy",
         elder_type: str = "priest", seed_name: str = "the elder") -> World:
    world = World(place)
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type=keeper_type,
        label=keeper_name,
        meters={"questing": 0.0, "travel": 0.0},
        memes={"devotion": 1.0, "fear": 0.0, "hope": 0.0, "fellowship": 0.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=seed_name,
        meters={"patience": 1.0},
        memes={"trust": 1.0},
    ))
    scroll = world.add(Entity(
        id="scripture",
        type="scroll",
        label="scripture",
        phrase="a cedar scroll of old verses",
        owner=keeper.id,
        keeper=elder.id,
        meters={"safe": 1.0, "creased": 0.0, "at_risk": 0.0},
    ))
    traveler = world.add(Entity(
        id="traveler",
        kind="character",
        type="woman",
        label="a desert traveler",
        meters={"journey": 1.0},
        memes={"memory": 1.0, "kindness": 1.0},
    ))
    helper_ent = world.add(Entity(
        id=helper.id,
        type="helper",
        label=helper.label,
        phrase=helper.teaches,
    ))

    world.say(
        f"In the old place called {place.label}, the keeper Ari tended the scripture like a small fire."
    )
    world.say(
        f"{keeper.pronoun().capitalize()} loved the old words and hoped to read them aloud at the moon rite."
    )
    world.say(
        f"Each evening, {keeper.pronoun()} listened as the elder spoke of the scripture's first bright promise."
    )

    world.para()
    keeper.memes["fear"] += 1
    keeper.meters["questing"] += 1
    scroll.meters["safe"] = 0
    propagate(world, narrate=False)
    world.say(
        f"But one dawn, the cedar chest stood open, and the scripture was gone."
    )
    world.say(
        f"Ari felt a hard ache in {keeper.pronoun('possessive')} chest and began a quest across the windy hills."
    )
    world.say(
        f"{keeper.pronoun().capitalize()} followed old footprints, asking stones and crows if they had seen the missing verses."
    )

    world.para()
    if helper.resolve == "share":
        world.say(
            f"Near the river gate, Ari met {traveler.label}, who knew a fragment of the holy lines."
        )
        world.say(
            f"{traveler.label.capitalize()} said the verse was not meant to stay hidden, but to be shared until it found its way home."
        )
        keeper.memes["fellowship"] += 1
        keeper.memes["hope"] += 1
        world.say(
            f"So Ari sat beside the traveler, and together they shared bread, water, and the first half of the scripture."
        )
        world.say(
            f"As the words were spoken aloud, the memory of the path grew clear in the keeper's mind."
        )

    world.para()
    scroll.meters["safe"] = 1.0
    scroll.meters["at_risk"] = 0.0
    keeper.memes["fear"] = 0.0
    keeper.memes["hope"] += 1
    keeper.memes["fellowship"] += 1
    world.say(
        f"At last Ari returned to the temple with the traveler, and the elder opened the cedar chest again."
    )
    world.say(
        f"The scripture lay warm in {keeper.pronoun('possessive')} hands, and this time the keeper did not hide it."
    )
    world.say(
        f"{keeper.pronoun().capitalize()} read the verses aloud for everyone, and the hall shone with quiet joy."
    )
    world.say(
        f"By sharing the scripture, Ari had not lost it at all; {keeper.pronoun()} had learned how to carry it together."
    )

    world.facts.update(
        keeper=keeper,
        elder=elder,
        scroll=scroll,
        traveler=traveler,
        helper=helper_ent,
        quest=quest,
        place=place,
        shared=True,
        resolved=True,
    )
    return world


PLACES = {
    "temple": Place(
        id="temple",
        label="the temple hill",
        affords={"seek", "share"},
        near={"river", "gate", "cedar_chest"},
    ),
    "river_gate": Place(
        id="river_gate",
        label="the river gate",
        affords={"seek", "share"},
        near={"temple", "road"},
    ),
    "road": Place(
        id="road",
        label="the long road",
        affords={"seek"},
        near={"river_gate", "temple"},
    ),
}

QUESTS = {
    "lost_scroll": Quest(
        id="lost_scroll",
        verb="recover the scripture",
        gerund="searching for the scripture",
        risk="the scripture is missing",
        damage="lost to wind and dust",
        keyword="scripture",
        tags={"scripture", "quest"},
    ),
    "missing_verse": Quest(
        id="missing_verse",
        verb="find the missing verse",
        gerund="hunting for the missing verse",
        risk="a verse cannot be remembered alone",
        damage="forgotten",
        keyword="scripture",
        tags={"scripture", "quest"},
    ),
}

HELPERS = {
    "traveler": Helper(
        id="traveler",
        label="a desert traveler",
        teaches="half a verse remembered by heart",
        carries="water and bread",
        resolve="share",
    ),
    "chorus": Helper(
        id="chorus",
        label="a village chorus",
        teaches="many voices that can finish one line",
        carries="song",
        resolve="share",
    ),
}

NAMES = ["Ari", "Mira", "Taro", "Levi", "Sela", "Nia", "Koa", "Ira"]
TRAITS = ["gentle", "brave", "curious", "steadfast", "quiet"]


@dataclass
class StoryParams:
    place: str
    quest: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            for hid, helper in HELPERS.items():
                if quest_at_risk(quest) and select_helper(quest, helper):
                    combos.append((pid, qid, hid))
    return combos


KNOWLEDGE = {
    "scripture": [
        ("What is scripture?",
         "Scripture is a holy writing that people read carefully because they believe its words matter deeply.")
    ],
    "quest": [
        ("What is a quest?",
         "A quest is a journey to find something, solve a problem, or do an important task.")
    ],
    "share": [
        ("What does it mean to share something?",
         "To share means to let other people use, hear, or enjoy something with you.")
    ],
    "river": [
        ("What is a river?",
         "A river is a moving stream of water that flows across the land.")
    ],
    "temple": [
        ("What is a temple?",
         "A temple is a special building where people gather for prayer, teaching, or worship.")
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about "{f["scroll"].label}", a quest, and sharing.',
        f"Tell a gentle myth where {f['keeper'].label} loses a scripture and learns to share it with a traveler.",
        f"Write a story in a mythic style about a holy scroll, a search across the road, and a happy return.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    keeper = f["keeper"]
    elder = f["elder"]
    scroll = f["scroll"]
    traveler = f["traveler"]
    return [
        QAItem(
            question=f"Who began the quest when the scripture disappeared from the cedar chest?",
            answer=f"{keeper.label} began the quest after the scripture went missing, because {keeper.pronoun()} wanted to bring it back for the moon rite.",
        ),
        QAItem(
            question=f"Why did {keeper.label} feel worried at the start of the story?",
            answer=f"{keeper.label} felt worried because the scripture was gone, and the sacred words could not be read aloud until it was found.",
        ),
        QAItem(
            question=f"Who helped {keeper.label} remember the way home?",
            answer=f"A desert traveler helped by sharing a remembered verse, which gave {keeper.label} hope and pointed the way back to the temple.",
        ),
        QAItem(
            question=f"What did the elder do when {keeper.label} returned?",
            answer=f"The elder opened the cedar chest again and listened while {keeper.label} read the scripture aloud for everyone.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the scripture was safe again, and {keeper.label} learned that sharing the holy words made them stronger, not smaller.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in {"scripture", "quest", "share"}:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="temple", quest="lost_scroll", helper="traveler", name="Ari", gender="boy", trait="gentle"),
    StoryParams(place="river_gate", quest="missing_verse", helper="traveler", name="Mira", gender="girl", trait="curious"),
]


def explain_rejection(quest: Quest, helper: Helper) -> str:
    return (
        f"(No story: the quest '{quest.id}' does not create a real scripture problem, "
        f"or the helper '{helper.id}' cannot solve it by sharing. The myth needs a holy text at risk "
        f"and a sharing-based turn.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if "scripture" in q.tags:
            lines.append(asp.fact("needs_scripture", qid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("resolve", hid, h.resolve))
    return "\n".join(lines)


ASP_RULES = r"""
quest_valid(P, Q, H) :- place(P), quest(Q), helper(H), needs_scripture(Q), resolve(H, share), affords(P, seek).
quest_story(P, Q, H) :- quest_valid(P, Q, H), affords(P, share).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_valid/3."))
    return sorted(set(asp.atoms(model, "quest_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic scripture quest storyworld with sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, helper = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        quest=quest,
        helper=helper,
        name=args.name or rng.choice(NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    helper = HELPERS[params.helper]
    world = tell(place, quest, helper, keeper_name=params.name, keeper_type="boy" if params.gender == "boy" else "girl")
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
        print(asp_program("#show quest_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid quest combos:\n")
        for p, q, h in combos:
            print(f"  {p:12} {q:14} {h}")
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
