#!/usr/bin/env python3
"""
A small storyworld about a spooky quest, a tiny ghost, and a fair way to
compensate when a brave idea goes wrong.

Seed tale sketch:
---
A child and a ghost set out on a quiet quest to find a lost silver bell.
The ghost glides too fast and snags a satin ribbon. The child says the ribbon
owner should be compensated, so they sneak back with a small gift. At the end,
the ghost learns to floss its teeth with a tiny thread after a sweet snack,
and the quest ends with both of them smiling in the moonlight.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        ghostish = {"ghost", "phantom"}
        if self.type in ghostish:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    mood: str = "moonlit"
    afford_quest: bool = True


@dataclass
class QuestItem:
    label: str
    phrase: str
    region: str
    value: int


@dataclass
class StoryParams:
    place: str
    quest_item: str
    hero_name: str
    hero_gender: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "house": Setting(place="the old house", mood="moonlit"),
    "attic": Setting(place="the attic", mood="dusty"),
    "cemetery": Setting(place="the quiet cemetery", mood="moonlit"),
    "garden": Setting(place="the moon garden", mood="foggy"),
}

QUEST_ITEMS = {
    "bell": QuestItem(label="bell", phrase="a silver bell", region="hand", value=3),
    "key": QuestItem(label="key", phrase="an old brass key", region="hand", value=2),
    "lantern": QuestItem(label="lantern", phrase="a small lantern", region="hand", value=4),
}

GHOST_TITLES = ["Moss", "Murmur", "Willow", "Pip", "Thistle"]
HERO_NAMES = ["Nina", "Milo", "June", "Toby", "Lena", "Ari"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

class WorldState:
    def __init__(self) -> None:
        self.quest_started = False
        self.ribbon_snagged = False
        self.compensated = False
        self.flossed = False
        self.quest_complete = False


def ghost_phrase(name: str) -> str:
    return f"{name}, a small ghost with a whisper-soft voice"


def story_opening(world: World, hero: Entity, ghost: Entity, item: Entity) -> None:
    world.say(
        f"On a moonlit night in {world.setting.place}, {hero.id} met {ghost_phrase(ghost.id)}."
    )
    world.say(
        f"They were on a quiet quest to find {item.phrase}, because the old house had hidden it for years."
    )


def begin_quest(state: WorldState, world: World, hero: Entity, ghost: Entity, item: Entity) -> None:
    state.quest_started = True
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    ghost.memes["hope"] = ghost.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} held a little lamp, and {ghost.id} floated ahead to guide the way through the dark halls."
    )


def snag_event(state: WorldState, world: World, hero: Entity, ghost: Entity) -> None:
    state.ribbon_snagged = True
    ghost.memes["embarrassment"] = ghost.memes.get("embarrassment", 0) + 1
    world.say(
        f"But the ghost drifted too fast and snagged a satin ribbon on a rusty nail."
    )
    world.say(
        f"{hero.id} gasped, because the ribbon belonged to a tiny doll on a shelf."
    )


def compensate_event(state: WorldState, world: World, hero: Entity, ghost: Entity) -> None:
    state.compensated = True
    hero.memes["fairness"] = hero.memes.get("fairness", 0) + 1
    ghost.memes["guilt"] = ghost.memes.get("guilt", 0) + 1
    world.say(
        f'{hero.id} said, "We should compensate the doll for the torn ribbon."'
    )
    world.say(
        f"So they left a shiny button and a folded note that promised, 'Sorry for the snag.'"
    )


def floss_event(state: WorldState, world: World, hero: Entity, ghost: Entity) -> None:
    state.flossed = True
    ghost.memes["pride"] = ghost.memes.get("pride", 0) + 1
    world.say(
        f"Later, after a sweet cake crumb from the kitchen, {ghost.id} tried flossing with a tiny thread."
    )
    world.say(
        f"{hero.id} laughed softly when the thread swayed like a silver spiderweb between ghostly fingers."
    )


def resolve(state: WorldState, world: World, hero: Entity, ghost: Entity, item: Entity) -> None:
    state.quest_complete = True
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    ghost.memes["peace"] = ghost.memes.get("peace", 0) + 1
    world.say(
        f"In the end, they found {item.phrase} tucked inside a cracked tea tin."
    )
    world.say(
        f"{hero.id} and {ghost.id} carried it back together, and the night felt gentle instead of spooky."
    )
    world.say(
        f"By dawn, the ribbon was mended, the quest was complete, and {ghost.id} was still smiling after its flossing lesson."
    )


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def tell(setting: Setting, quest_item: QuestItem, hero_name: str, ghost_name: str, hero_gender: str) -> World:
    world = World(setting)
    state = WorldState()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    ghost = world.add(Entity(id=ghost_name, kind="character", type="ghost"))
    item = world.add(Entity(id=quest_item.label, type=quest_item.label, label=quest_item.label, phrase=quest_item.phrase))

    story_opening(world, hero, ghost, item)
    world.para()
    begin_quest(state, world, hero, ghost, item)
    snag_event(state, world, hero, ghost)
    compensate_event(state, world, hero, ghost)
    world.para()
    floss_event(state, world, hero, ghost)
    resolve(state, world, hero, ghost, item)

    world.facts.update(
        hero=hero,
        ghost=ghost,
        item=item,
        state=state,
        quest_item=quest_item,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    ghost: Entity = f["ghost"]
    item: Entity = f["item"]
    return [
        'Write a short ghost story for a child about a quest, a mistake, and a fair way to compensate.',
        f"Tell a moonlit story where {hero.id} and {ghost.id} search for {item.phrase} and fix a torn ribbon kindly.",
        f"Write a gentle spooky story that includes the words 'quest', 'compensate', and 'floss'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ghost: Entity = f["ghost"]
    item: Entity = f["item"]
    state: WorldState = f["state"]
    qas = [
        QAItem(
            question=f"What were {hero.id} and {ghost.id} looking for?",
            answer=f'They were on a quiet quest to find {item.phrase} in {world.setting.place}.',
        ),
        QAItem(
            question=f"Why did {hero.id} say they should compensate the doll?",
            answer="Because the ghost snagged a satin ribbon on a rusty nail, and the ribbon belonged to the doll.",
        ),
        QAItem(
            question=f"What did {ghost.id} do with a tiny thread after the sweet snack?",
            answer="It tried flossing with a tiny thread, and the thread swayed like a silver spiderweb.",
        ),
    ]
    if state.compensated:
        qas.append(
            QAItem(
                question=f"How did {hero.id} and {ghost.id} make up for the torn ribbon?",
                answer="They left a shiny button and a folded note that said sorry for the snag.",
            )
        )
    if state.quest_complete:
        qas.append(
            QAItem(
                question=f"How did the story end for {hero.id} and {ghost.id}?",
                answer=f"They carried {item.phrase} back together, and the night felt gentle instead of spooky.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or solve a problem.",
        ),
        QAItem(
            question="What does compensate mean?",
            answer="To compensate means to make up for a mistake or loss with something fair or helpful.",
        ),
        QAItem(
            question="What is floss used for?",
            answer="Floss is a thin thread used to clean between teeth where a brush cannot easily reach.",
        ),
        QAItem(
            question="Why do ghost stories often feel spooky?",
            answer="Ghost stories feel spooky because they use dark places, quiet nights, and mysterious surprises.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
ghost(G) :- ghost_name(G).
quest_item(I) :- item_name(I).

quest_started :- hero(_), ghost(_), quest_item(_).
snagged :- quest_started, ribbon_torn.
compensated :- snagged, fair_fix.
flossed :- ghost(_), floss_tool(_), sweet_snack.
quest_complete :- quest_started, compensated, flossed.

#show quest_started/0.
#show snagged/0.
#show compensated/0.
#show flossed/0.
#show quest_complete/0.
"""


def asp_facts() -> str:
    import asp
    f = []
    for name in HERO_NAMES:
        f.append(asp.fact("hero_name", name))
    for name in GHOST_TITLES:
        f.append(asp.fact("ghost_name", name))
    for item in QUEST_ITEMS:
        f.append(asp.fact("item_name", item))
    f.append(asp.fact("ribbon_torn"))
    f.append(asp.fact("fair_fix"))
    f.append(asp.fact("floss_tool"))
    f.append(asp.fact("sweet_snack"))
    return "\n".join(f)


def asp_program(show: str = "#show quest_complete/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_started/0. #show snagged/0. #show compensated/0. #show flossed/0. #show quest_complete/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    wanted = {"quest_started/0", "snagged/0", "compensated/0", "flossed/0", "quest_complete/0"}
    if atoms == wanted:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH:", sorted(atoms), "!=", sorted(wanted))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story world with a quest, compensation, and flossing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--ghost-name", choices=GHOST_TITLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    quest_item = args.quest_item or rng.choice(list(QUEST_ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_TITLES)
    if args.quest_item and args.quest_item not in QUEST_ITEMS:
        raise StoryError("Unknown quest item.")
    return StoryParams(place=place, quest_item=quest_item, hero_name=name, hero_gender=gender, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUEST_ITEMS[params.quest_item], params.hero_name, params.ghost_name, params.hero_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    f = world.facts["state"]
    lines.append(
        f"  state: quest_started={f.quest_started} ribbon_snagged={f.ribbon_snagged} "
        f"compensated={f.compensated} flossed={f.flossed} quest_complete={f.quest_complete}"
    )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(place="house", quest_item="bell", hero_name="Nina", hero_gender="girl", ghost_name="Murmur"),
    StoryParams(place="attic", quest_item="key", hero_name="Milo", hero_gender="boy", ghost_name="Willow"),
    StoryParams(place="garden", quest_item="lantern", hero_name="June", hero_gender="girl", ghost_name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_complete/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_started/0. #show snagged/0. #show compensated/0. #show flossed/0. #show quest_complete/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
