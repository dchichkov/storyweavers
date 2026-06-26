#!/usr/bin/env python3
"""
pyramid_reconciliation_adventure.py

A small story world about a pyramid adventure that turns into reconciliation.
A child, a companion, a careful search, a tense disagreement, and a shared fix
produce a complete, state-driven story.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    weather: str
    keyword: str = "pyramid"
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    label: str
    phrase: str
    type: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _turn_end(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("hurt", 0.0) >= THRESHOLD and ent.memes.get("kindness", 0.0) >= THRESHOLD:
            sig = ("reconcile", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["hurt"] = 0.0
            ent.memes["peace"] = ent.memes.get("peace", 0.0) + 1.0
            out.append("They stopped, looked at each other, and the angry feeling loosened.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for sent in _turn_end(world):
            produced.append(sent)
            changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_story() -> tuple[dict[str, Setting], dict[str, Quest], dict[str, Token], dict[str, Gear]]:
    settings = {
        "desert": Setting(place="the desert path", affords={"explore"}),
        "museum": Setting(place="the pyramid museum", indoor=True, affords={"explore"}),
        "ruins": Setting(place="the old pyramid ruins", affords={"explore"}),
    }
    quests = {
        "explore": Quest(
            id="explore",
            verb="explore the pyramid",
            gerund="exploring the pyramid",
            rush="dash deeper into the hall",
            risk="dust and worry",
            zone={"feet", "hands", "torso"},
            weather="sunny",
            tags={"pyramid", "adventure"},
        ),
    }
    tokens = {
        "scarf": Token(label="scarf", phrase="a bright red scarf", type="scarf", region="torso"),
        "hat": Token(label="hat", phrase="a woven sun hat", type="hat", region="head"),
        "map": Token(label="map", phrase="a folded map", type="map", region="hands"),
    }
    gear = {
        "lantern": Gear(
            id="lantern",
            label="a small lantern",
            covers={"hands", "torso"},
            helps={"dust"},
            prep="carry a small lantern together",
            tail="walked slowly with the lantern between them",
        ),
        "gloves": Gear(
            id="gloves",
            label="soft gloves",
            covers={"hands"},
            helps={"dust"},
            prep="put on soft gloves first",
            tail="kept their hands steady and clean",
        ),
        "scarf": Gear(
            id="scarfgear",
            label="a scarf over the mouth",
            covers={"torso"},
            helps={"dust"},
            prep="wrap a scarf over their mouths",
            tail="could breathe easier in the dusty passage",
        ),
    }
    return settings, quests, tokens, gear


SETTINGS, QUESTS, TOKENS, GEAR = setup_story()

GIRL_NAMES = ["Maya", "Lina", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Leo"]
TRAITS = ["brave", "curious", "careful", "spirited", "restless"]


def exploration_reconciles(settlement: Setting, quest: Quest) -> bool:
    return quest.id in settlement.affords


def select_gear(quest: Quest, token: Token) -> Optional[Gear]:
    for g in GEAR.values():
        if token.region in g.covers and "dust" in g.helps:
            return g
    return None


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for r in sorted(q.zone):
            lines.append(asp.fact("splashes", qid, r))
        lines.append(asp.fact("risk", qid, "dust"))
    for tid, t in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("worn_on", tid, t.region))
        for g in sorted(t.genders):
            lines.append(asp.fact("wears", g, tid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Q,T) :- affords(Place,Q), risk(Q,dust), worn_on(T,R), splashes(Q,R), token(T).
fix(Q,T,G) :- valid(_,Q,T), gear(G), worn_on(T,R), covers(G,R), helps(G,dust).
valid_story(Place,Q,T,Gender) :- valid(Place,Q,T), wears(Gender,T), fix(Q,T,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    place: str
    quest: str
    token: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for qid in s.affords:
            q = QUESTS[qid]
            for tid, t in TOKENS.items():
                if q.zone and t.region in q.zone:
                    out.append((place, qid, tid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pyramid adventure with reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["friend", "sibling"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.token is None or c[2] == args.token)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, token = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    token_obj = TOKENS[token]
    if gender not in token_obj.genders:
        raise StoryError("That token does not fit the chosen gender in this world.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        quest=quest,
        token=token,
        name=name,
        gender=gender,
        companion=args.companion or rng.choice(["friend", "sibling"]),
        trait=rng.choice(TRAITS),
    )


def build_world(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    pal_name = "Tia" if params.companion == "friend" else "Jude"
    pal_type = "girl" if params.companion == "friend" else "boy"
    pal = world.add(Entity(id=pal_name, kind="character", type=pal_type, traits=["helpful"]))
    token = world.add(Entity(id="token", type=TOKENS[params.token].type, label=TOKENS[params.token].label, owner=hero.id))
    token.worn_by = hero.id
    quest = QUESTS[params.quest]
    gear = select_gear(quest, TOKENS[params.token])

    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved adventures.")
    world.say(f"{hero.id} and {pal.id} wanted to {quest.verb} near {world.setting.place}.")
    world.say(f"{hero.id} wore {TOKENS[params.token].phrase} because it felt special for the trip.")
    world.para()

    world.say(f"Inside the pyramid, the air felt warm and dusty.")
    hero.memes["curiosity"] = 1.0
    pal.memes["curiosity"] = 1.0
    world.zone = set(quest.zone)
    world.say(f"{hero.id} wanted to {quest.rush}, but {pal.id} slowed down and pointed at a narrow path.")
    hero.memes["impatient"] = 1.0
    pal.memes["care"] = 1.0
    world.say(f"They argued for a moment, and the excited feeling turned sharp.")
    hero.memes["hurt"] = 1.0
    pal.memes["hurt"] = 1.0

    if gear is not None:
        world.para()
        world.say(f"{pal.id} held up {gear.label} and said, \"Let's share it so we can go on safely.\"")
        world.say(f"{hero.id} paused, breathed out, and nodded.")
        hero.memes["kindness"] = 1.0
        pal.memes["kindness"] = 1.0
        world.say(f"They used {gear.prep} and kept going together.")
        propagate(world, narrate=True)
        world.say(f"At the end, {hero.id} and {pal.id} smiled beside the pyramid, feeling close again.")
    else:
        world.para()
        world.say(f"They stopped and chose a slower way, so the hurt feeling faded on its own.")
        hero.memes["kindness"] = 1.0
        pal.memes["kindness"] = 1.0
        propagate(world, narrate=True)

    world.facts.update(hero=hero, pal=pal, token=token, quest=quest, gear=gear, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a short adventure story for a child about a pyramid and a gentle reconciliation.',
        f"Tell a story where {hero.id} wants to {quest.verb} but learns to share and keep going.",
        f'Write a simple story that includes the word "pyramid" and ends with friends or siblings making up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    quest = f["quest"]
    token = f["token"]
    out = [
        QAItem(
            question=f"Who went to the pyramid with {hero.id}?",
            answer=f"{pal.id} went with {hero.id}, and they explored together.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the pyramid?",
            answer=f"{hero.id} wanted to {quest.verb}.",
        ),
        QAItem(
            question=f"What special thing did {hero.id} wear on the trip?",
            answer=f"{hero.id} wore {token.label}, which made the trip feel special.",
        ),
    ]
    if f.get("gear") is not None:
        gear = f["gear"]
        out.append(QAItem(
            question=f"How did {gear.label} help the two friends or siblings?",
            answer=f"It helped them move more carefully and stay together while they went on with the adventure.",
        ))
    out.append(QAItem(
        question=f"What changed after they disagreed in the pyramid?",
        answer="They calmed down, chose a safer way, and felt close again by the end.",
    ))
    return out


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a pyramid?",
        answer="A pyramid is a big stone building with sloping sides and a point at the top.",
    ),
    QAItem(
        question="Why can old ruins feel dusty?",
        answer="Old ruins can feel dusty because tiny bits of stone and sand can collect there over time.",
    ),
    QAItem(
        question="What does it mean to reconcile?",
        answer="To reconcile means to make up after a disagreement and feel friendly again.",
    ),
    QAItem(
        question="Why is adventure exciting?",
        answer="Adventure is exciting because it lets people explore new places, solve problems, and find something interesting.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
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


def valid_story_params() -> list[StoryParams]:
    out = []
    for place, qid, tid in valid_combos():
        for gender in TOKENS[tid].genders:
            out.append(StoryParams(place=place, quest=qid, token=tid, name="Mia", gender=gender, companion="friend", trait="curious"))
    return out


def asp_valid_combos_only() -> list[tuple]:
    import asp

    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid")))


def asp_valid_stories_only() -> list[tuple]:
    import asp

    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos_only()
        stories = asp_valid_stories_only()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):")
        for place, qid, tid in triples:
            genders = sorted(g for (p, q, t, g) in stories if (p, q, t) == (place, qid, tid))
            print(f"  {place:18} {qid:8} {tid:8} [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in valid_story_params():
            samples.append(build_world(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = build_world(params)
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
            header = f"### {p.name}: {p.quest} at {p.place} ({p.token})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.token:
        q = QUESTS[args.quest]
        t = TOKENS[args.token]
        if t.region not in q.zone:
            raise StoryError("That token does not fit the quest's safe region.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.token is None or c[2] == args.token)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, token = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(TOKENS[token].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        quest=quest,
        token=token,
        name=name,
        gender=gender,
        companion=args.companion or rng.choice(["friend", "sibling"]),
        trait=rng.choice(TRAITS),
    )


if __name__ == "__main__":
    main()
