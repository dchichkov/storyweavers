#!/usr/bin/env python3
"""
A standalone story world for a tiny fable-style quest about sharp things,
being upset, rhyme, and sound effects.

Seed image:
---
A small fox wants to finish a quest to bring home a bright berry basket.
A sharp bramble scratches the fox, making the fox upset.
A clever friend offers a safer rhyme and a quieter path, and the fox learns
to ask for help instead of rushing ahead.

World model:
---
- Physical meters track scratch, strain, and treasure carrying.
- Emotional memes track upset, courage, relief, and friendship.
- Sound effects are treated as narrated events, not just decoration.
- The story turns when the hero changes method: from rushing in to choosing
  a careful rhyme-guided path.

The domain is intentionally small and constraint-checked: a quest must have a
sharp hazard, an upset response, and a believable safer alternative.
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
# Domain entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "girl", "mother", "woman"}
        male = {"boy", "father", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the briar path"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    rhyme: str
    rush: str
    prize: str
    sound: str
    hazard: str
    tag: str
    safer: str


@dataclass
class Shield:
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.zone = set(self.zone)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "briar_path": Setting(place="the briar path", affords={"berry_quest"}),
    "wood_edge": Setting(place="the wood's edge", affords={"berry_quest"}),
    "hill_lane": Setting(place="the hill lane", affords={"berry_quest"}),
}

QUESTS = {
    "berry_basket": Quest(
        id="berry_basket",
        goal="bring home the berry basket",
        rhyme="bramble, bramble, sharp and tall, don't make a little traveler fall",
        rush="dash through the brambles",
        prize="a basket of bright berries",
        sound="snip-snap",
        hazard="sharp",
        tag="berry",
        safer="walk with care and sing the rhyme",
    ),
    "star_flower": Quest(
        id="star_flower",
        goal="carry back the star flower",
        rhyme="petal, petal, soft and light, keep your steps both kind and right",
        rush="hurry through the thistles",
        prize="a star-shaped flower",
        sound="zip-zip",
        hazard="sharp",
        tag="flower",
        safer="take the smooth side of the path",
    ),
}

SHIELDS = [
    Shield(
        id="thick_cloak",
        label="a thick cloak",
        covers={"torso"},
        guards={"sharp"},
        prep="put on a thick cloak first",
        tail="walked on more slowly with the cloak tucked close",
    ),
    Shield(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"sharp"},
        prep="pull on soft gloves first",
        tail="held the basket more safely with the gloves on",
        plural=True,
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Tessa", "Nora", "Pip"]
BOY_NAMES = ["Rowan", "Bram", "Owen", "Finn", "Ash"]
TRAITS = ["brave", "curious", "gentle", "stubborn", "cheerful"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def has_hazard(quest: Quest) -> bool:
    return quest.hazard == "sharp"


def quest_at_risk(quest: Quest) -> bool:
    return has_hazard(quest)


def select_shield(quest: Quest) -> Optional[Shield]:
    for shield in SHIELDS:
        if quest.hazard in shield.guards:
            return shield
    return None


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("scratch", 0) < 1:
            continue
        sig = ("upset", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["upset"] = actor.memes.get("upset", 0) + 1
        out.append(f"{actor.id} winced and felt upset.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_quest(world: World, hero: Entity, quest: Quest) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    return {
        "scratched": sim.get(hero.id).meters.get("scratch", 0) > 0,
        "upset": sim.get(hero.id).memes.get("upset", 0) > 0,
    }


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in {"berry_basket", "star_flower"}:
        return
    world.zone = {"hands", "torso"}
    hero.meters["scratch"] = hero.meters.get("scratch", 0) + 1
    if narrate:
        world.say(f"{quest.sound}! {hero.id} brushed a sharp bramble.")
    propagate(world, narrate=narrate)


def tell(setting: Setting, quest: Quest, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="Prize", type="thing", label=quest.prize, phrase=quest.prize, owner=hero.id))
    shield = None

    hero.memes["courage"] = 1
    hero.memes["hope"] = 1
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved a good quest.")
    world.say(f"{hero.id} wanted {quest.goal}, and {quest.rhyme} was a rhyme {hero.pronoun('subject')} liked to hum.")
    world.say(f"At {setting.place}, {hero.id} carried {prize.phrase} and listened for the path's soft sounds.")

    world.para()
    world.say(f"One day, {hero.id} went to {setting.place} with {hero.pronoun('possessive')} {parent.label}.")
    world.say(f"{hero.id} wanted to {quest.rush}, but the brambles were sharp and close.")
    world.say(f"{quest.sound}! A thorn scratched {hero.pronoun('object')}.")

    _do_quest(world, hero, quest, narrate=True)

    if hero.memes.get("upset", 0) > 0:
        world.say(f"{hero.id} felt upset and nearly dropped the prize.")
        world.say(f"{parent.label.capitalize()} said, \"Slow paws, small heart. Listen to the rhyme.\"")

    shield = select_shield(quest)
    world.para()
    if shield:
        shield_ent = world.add(Entity(
            id=shield.id, type="gear", label=shield.label, protective=True,
            owner=hero.id, plural=shield.plural
        ))
        hero.meters["scratch"] = 0
        hero.memes["upset"] = 0
        world.say(f"{hero.id}'s {parent.label} chose to {shield.prep}.")
        world.say(f"Then {hero.id} could {quest.safer}, and the sharp brambles could not bother {hero.pronoun('object')} anymore.")
        world.say(f"{hero.id} whispered the rhyme: \"{quest.rhyme}.\"")
        world.say(f"{quest.sound}! This time, {hero.id} came home with {prize.phrase}, and {hero.id} was smiling.")
        world.facts["shield"] = shield_ent
        world.facts["resolved"] = True
    else:
        world.say(f"There was no safe shield for this quest, so {hero.id} had to turn back and try another day.")
        world.facts["resolved"] = False

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        quest=quest,
        setting=setting,
        trait=trait,
        hero_type=hero_type,
        parent_type=parent_type,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for qid, quest in QUESTS.items():
        if quest_at_risk(quest) and select_shield(quest):
            for sid in SETTINGS:
                out.append((sid, qid))
    return out


ASP_RULES = r"""
quest_at_risk(Q) :- quest(Q), hazard(Q, sharp).
has_shield(Q) :- quest_at_risk(Q), shield(S), guards(S, sharp).
valid(Set, Q) :- setting(Set), affords(Set, Q), quest_at_risk(Q), has_shield(Q).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("hazard", qid, quest.hazard))
    for shield in SHIELDS:
        lines.append(asp.fact("shield", shield.id))
        for g in sorted(shield.guards):
            lines.append(asp.fact("guards", shield.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world with a sharp upset quest and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.setting and args.quest and (args.setting, args.quest) not in combos:
        raise StoryError("No valid fable story matches the given setting and quest.")
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.quest is None or c[1] == args.quest)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    setting, quest = rng.choice(sorted(filtered))
    q = QUESTS[quest]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a short fable for children about a {hero.type} named {hero.id} on a {quest.goal} quest.',
        f"Tell a gentle story with rhyme and sound effects where {hero.id} meets something sharp and gets upset, then finds a safer way.",
        f'Write a simple quest story that includes the words "sharp" and "upset" and ends with a lesson about slowing down.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, quest = f["hero"], f["parent"], f["quest"]
    trait = f["trait"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {trait} {hero.type}, and {hero.pronoun('possessive')} {parent.label if hasattr(parent, 'label') else 'parent'} on a quest.",
        ),
        QAItem(
            question=f"What made {hero.id} upset?",
            answer=f"A sharp bramble scratched {hero.pronoun('object')} with a {quest.sound} sound, and that made {hero.id} upset.",
        ),
        QAItem(
            question=f"What rhyme did {hero.id} use to stay safe?",
            answer=f"{quest.rhyme.capitalize()}. That rhyme helped {hero.id} slow down and choose a safer path.",
        ),
    ]
    if f.get("resolved"):
        shield = f["shield"]
        qa.append(QAItem(
            question=f"How did {shield.label} help?",
            answer=f"{shield.label.capitalize()} helped because it let {hero.id} keep going without another scratch, so the quest could finish safely.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharp mean?",
            answer="Sharp means able to cut, poke, or scratch easily.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a short bit of language with matching ending sounds that can be easy to remember.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word like snip or snap that helps you imagine a noise in the scene.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone tries to reach a goal.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    world = tell(setting, quest, params.name, params.gender, params.parent, params.trait)
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
    StoryParams(setting="briar_path", quest="berry_basket", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="wood_edge", quest="star_flower", name="Rowan", gender="boy", parent="father", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
            header = f"### {p.name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
