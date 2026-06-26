#!/usr/bin/env python3
"""
storyworlds/worlds/hub_chum_gag_lesson_learned_humor_folk.py
=============================================================

A folk-tale sketch about a silly village hub, a chum's wild idea, and a gag
that teaches a lesson.  The domain is a small market hub where friends meet.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"trickster", "farmer", "mayor", "chum"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Parameter knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the hub"
    hub_kind: str = "village well"
    detail: str = "clay jars"
    affords: set[str] = field(default_factory=set)


@dataclass
class Gag:
    id: str
    name: str
    verb: str
    result: str
    flaw: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HubItem:
    label: str
    phrase: str
    type: str
    fragile: bool = True
    gets_ruined: bool = True


SETTINGS = {
    "well": Setting(place="the old well", hub_kind="village well", detail="clay jars",
                    affords={"pie", "frog", "hat"}),
    "market": Setting(place="the dusty market", hub_kind="market square", detail="wooden crates",
                      affords={"pie", "frog"}),
    "barn": Setting(place="the big barn", hub_kind="barn", detail="hay bales",
                    affords={"hat", "frog"}),
}

GAGS = {
    "pie": Gag(
        id="pie", name="a cream pie",
        verb="sneak a cream pie from the sill",
        result="the pie splattered everywhere with a SPLAT",
        flaw="the chum slipped on a banana peel and the pie flew sideways",
        lesson="a gag is only funny when nobody gets hurt",
        tags={"messy", "silly"},
    ),
    "frog": Gag(
        id="frog", name="a jumping frog",
        verb="hide a jumping frog in the hub",
        result="the frog leaped onto every head and croaked loudly",
        flaw="the frog got stuck in a bucket and croaked all day",
        lesson="a good joke needs a good escape plan",
        tags={"animal", "surprise"},
    ),
    "hat": Gag(
        id="hat", name="a floppy hat",
        verb="put a floppy hat on the hub sign",
        result="the hat fell over everyone's eyes and they bumped into each other",
        flaw="the hat was too big and smothered the sign completely",
        lesson="sometimes the best laugh comes from the simplest trick",
        tags={"silly", "clothing"},
    ),
}

HUB_ITEMS = {
    "jar": HubItem(label="clay jar", phrase="a painted clay jar", type="jar"),
    "crate": HubItem(label="wooden crate", phrase="a wobbly wooden crate", type="crate"),
    "sign": HubItem(label="hub sign", phrase="the creaky hub sign", type="sign",
                    fragile=False, gets_ruined=False),
}

CHARACTER_NAMES = {
    "trickster": ["Finn", "Jest", "Wink", "Grinn"],
    "chum": ["Bram", "Pip", "Tuck", "Moss"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id in SETTINGS:
        setting = SETTINGS[place_id]
        for gag_id in setting.affords:
            gag = GAGS[gag_id]
            for item_id, item in HUB_ITEMS.items():
                if item.fragile and gag.tags & {"messy", "animal"}:
                    combos.append((place_id, gag_id, item_id))
                elif not item.fragile:
                    combos.append((place_id, gag_id, item_id))
    return combos


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_gag_backfire(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["prank"] >= THRESHOLD and e.meters["clumsy"] >= THRESHOLD:
            sig = ("backfire", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["shame"] += 1
            out.append("A ripple of laughter spread through the hub as everyone watched.")
    return out


def _r_lesson_learned(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["shame"] >= THRESHOLD and e.memes["kindness"] < THRESHOLD:
            sig = ("lesson", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["wisdom"] += 1
            out.append("The trickster felt a warm glow instead of a mean one.")
    return out


CAUSAL_RULES = [
    Rule(name="backfire", apply=_r_gag_backfire),
    Rule(name="lesson", apply=_r_lesson_learned),
]


def propagate(world: World) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


# ---------------------------------------------------------------------------
# Storytelling verbs
# ---------------------------------------------------------------------------
def introduce_hub(world: World, hub_entity: Entity) -> None:
    world.say(f"In the middle of the village stood {world.setting.place}, "
              f"where {world.setting.detail} sat in tidy rows and friends gathered to chat.")


def introduce_trickster(world: World, trickster: Entity) -> None:
    world.say(f"{trickster.id} was known as the trickster of the {world.setting.hub_kind}, "
              f"always thinking of the next silly gag.")


def introduce_chum(world: World, chum: Entity) -> None:
    world.say(f"{chum.id} was {trickster.pronoun('possessive')} best chum, "
              f"a loyal friend who followed every wild idea with a grin.")


def plan_gag(world: World, trickster: Entity, chum: Entity, gag: Gag, item: HubItem) -> None:
    trickster.meters["prank"] += 1
    world.say(f"One morning, {trickster.id} whispered to {chum.id}, "
              f'"Let\'s {gag.verb} and watch what happens!"')
    world.say(f"{chum.id} nodded eagerly, {chum.pronoun('possessive')} eyes wide with excitement.")


def execute_gag(world: World, trickster: Entity, chum: Entity, gag: Gag) -> None:
    world.say(f"The duo snuck toward the {world.setting.place}. "
              f"{gag.result}, and the whole {world.setting.hub_kind} gasped.")
    chum.meters["clumsy"] += 1
    world.say(f"But then {chum.id} {gag.flaw}.")
    world.say(f"Suddenly, {gag.result} again, but this time right onto "
              f"{trickster.id}'s own head!")


def crowd_reaction(world: World, trickster: Entity, chum: Entity) -> None:
    world.say(f"Everyone at the {world.setting.hub_kind} burst into friendly laughter. "
              f"The joke had turned around!")


def moment_of_reflection(world: World, trickster: Entity, gag: Gag) -> None:
    world.say(f"{trickster.id} blushed and rubbed {trickster.pronoun('possessive')} head. "
              f'"I guess {gag.lesson}," {trickster.pronoun()} said with a sheepish smile.')


def happy_ending(world: World, trickster: Entity, chum: Entity) -> None:
    trickster.memes["wisdom"] += 1
    world.say(f"{chum.id} helped {trickster.id} clean up, and soon the two chums were "
              f"sitting by the {world.setting.hub_kind}, laughing about the whole affair "
              f"with the villagers. The {world.setting.place} was happy again.")


# ---------------------------------------------------------------------------
# The tell function
# ---------------------------------------------------------------------------
def tell(setting_id: str, gag_id: str, item_id: str,
         trickster_name: str = "Finn", chum_name: str = "Bram") -> World:
    setting = SETTINGS[setting_id]
    gag = GAGS[gag_id]
    item = HUB_ITEMS[item_id]
    world = World(setting)

    trickster = world.add(Entity(id=trickster_name, kind="character", type="trickster",
                                 traits=["silly", "clever"]))
    chum = world.add(Entity(id=chum_name, kind="character", type="chum",
                            traits=["loyal", "clumsy"]))
    hub_item = world.add(Entity(id="hub_item", kind="thing", type=item.type,
                                label=item.label, phrase=item.phrase))

    # Act 1: Hub introduction
    introduce_hub(world, hub_item)
    introduce_trickster(world, trickster)
    introduce_chum(world, chum)
    world.para()

    # Act 2: The gag
    plan_gag(world, trickster, chum, gag, item)
    execute_gag(world, trickster, chum, gag)
    propagate(world)
    world.para()

    # Act 3: Lesson learned with humor
    crowd_reaction(world, trickster, chum)
    moment_of_reflection(world, trickster, gag)
    happy_ending(world, trickster, chum)
    propagate(world)

    world.facts = dict(trickster=trickster, chum=chum, gag=gag,
                       setting=setting, item=item)
    return world


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    gag: str
    item: str
    trickster_name: str
    chum_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "hub": [("What is a village hub?", "A village hub is a place in the middle of "
             "town where people meet to talk and share news.")],
    "chum": [("What is a chum?", "A chum is a very close friend, someone you like "
              "to share silly jokes with.")],
    "silly": [("Why are silly jokes fun?", "Silly jokes make everyone laugh together, "
               "and laughing feels good.")],
    "gag": [("What is a gag in a story?", "A gag is a funny trick or joke that "
             "characters play on each other.")],
}


def generation_prompts(world: World) -> list[str]:
    gag = world.facts["gag"]
    return [
        f"Write a folk tale about a trickster and a chum at a village hub "
        f"and a silly gag that teaches a lesson.",
        f"Tell a humorous story about {gag.name} and what happens when a "
        f"prank goes wrong at the hub.",
        f"Create a short folk tale with a lesson learned about friendship "
        f"and laughter at the market hub.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    t, c, g = f["trickster"], f["chum"], f["gag"]
    return [
        QAItem(
            question=f"Who is the trickster at {f['setting'].place}?",
            answer=f"The trickster is {t.id}, a silly friend who loves to plan gags "
                   f"at the {f['setting'].hub_kind}."
        ),
        QAItem(
            question=f"What did {t.id} and {c.id} plan with {g.name}?",
            answer=f"They tried to {g.verb}, but {c.id} {g.flaw} and the gag "
                   f"turned into a laugh on themselves."
        ),
        QAItem(
            question=f"What lesson did {t.id} learn?",
            answer=f"{t.id} learned that {g.lesson} and that true laughter comes "
                   f"from kindness, not from getting others in trouble."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["gag"].tags)
    tags.add("hub")
    out = []
    for topic, qas in KNOWLEDGE.items():
        if topic in tags or topic in {"hub", "chum"}:
            out.append(QAItem(question=qas[0][0], answer=qas[0][1]))
    return out


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
affords_hub(H, G) :- hub(H), gag_hub(G), gag_at(H, G).
fits_item(G, I) :- gag(G), item(I), not fragile(I) ; fragile(I), messes_up(G).
valid(H, G, I) :- hub(H), gag_hub(G), fits_item(G, I).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for hid, s in SETTINGS.items():
        lines.append(asp.fact("hub", hid))
        for g in sorted(s.affords):
            lines.append(asp.fact("gag_hub", g))
            lines.append(asp.fact("gag_at", hid, g))
    for gid, g in GAGS.items():
        lines.append(asp.fact("gag", gid))
        for t in sorted(g.tags):
            if t == "messy":
                lines.append(asp.fact("messes_up", gid))
    for iid, it in HUB_ITEMS.items():
        lines.append(asp.fact("item", iid))
        if not it.fragile:
            lines.append(asp.fact("fragile", iid))
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    py_set = set(valid_combos())
    model = asp.one_model(asp_facts() + "\n" + ASP_RULES + "\n#show valid/3.")
    asp_set = set(asp.atoms(model, "valid"))
    if py_set == asp_set:
        print(f"OK: {len(py_set)} combos verified.")
        return 0
    print("Mismatch!")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk tale: hub, chum, and a gag that teaches a lesson.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--gag", choices=list(GAGS))
    ap.add_argument("--item", choices=list(HUB_ITEMS))
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
              and (args.gag is None or c[1] == args.gag)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("No valid combo with given options.")
    place, gag, item = rng.choice(sorted(combos))
    tn = args.trickster_name or rng.choice(CHARACTER_NAMES["trickster"])
    cn = args.chum_name or rng.choice(CHARACTER_NAMES["chum"])
    return StoryParams(place=place, gag=gag, item=item,
                       trickster_name=tn, chum_name=cn)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.gag, params.item,
                 params.trickster_name, params.chum_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"  {e.id}: meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print("\n=== Prompts ===")
        for p in sample.prompts:
            print(f"- {p}")
        print("\n=== Story QA ===")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}\n")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_facts())
        print(ASP_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        for combo in valid_combos():
            params = StoryParams(place=combo[0], gag=combo[1], item=combo[2],
                                 trickster_name="Finn", chum_name="Bram")
            samples.append(generate(params))
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 10, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"--- Story {i + 1} ---" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print()


if __name__ == "__main__":
    main()
