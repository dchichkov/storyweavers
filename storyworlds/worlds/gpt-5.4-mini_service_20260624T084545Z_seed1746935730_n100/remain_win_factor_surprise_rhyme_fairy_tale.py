#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a childlike hero, a surprise to solve,
and a rhyme that helps the good ending remain.

Seed premise:
- remain
- win
- factor
- Surprise
- Rhyme
- Fairy Tale
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "witch"}
        male = {"boy", "king", "prince", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def object_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    noun: str
    risk: str
    danger: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    helps: set[str]
    required_factor: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.current_quest: Optional[Quest] = None
        self.current_charm: Optional[Charm] = None

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "castle": Setting(place="the castle garden", mood="golden", affords={"quest", "rhyme"}),
    "forest": Setting(place="the whispering forest", mood="green", affords={"quest", "rhyme"}),
    "tower": Setting(place="the moonlit tower", mood="silver", affords={"quest", "rhyme"}),
}

QUESTS = {
    "rose": Quest(
        id="rose",
        verb="pick the glowing rose",
        noun="glowing rose",
        risk="the thorns might prick little hands",
        danger="thorns",
        clue="a humming bee",
        tags={"flower", "thorn", "surprise"},
    ),
    "crown": Quest(
        id="crown",
        verb="carry the lost crown",
        noun="lost crown",
        risk="it might slip and tumble into the moss",
        danger="slip",
        clue="a trail of glitter",
        tags={"crown", "king", "surprise"},
    ),
    "egg": Quest(
        id="egg",
        verb="guard the tiny egg",
        noun="tiny egg",
        risk="a bump could crack it",
        danger="crack",
        clue="a soft warm nest",
        tags={"egg", "nest", "surprise"},
    ),
}

CHARMS = {
    "cloak": Charm(
        id="cloak",
        label="a moon cloak",
        phrase="a moon cloak with a silver hem",
        helps={"thorns", "slip", "crack"},
        required_factor="surprise",
        prep="put on the moon cloak first",
        tail="walked on with the moon cloak bright around their shoulders",
    ),
    "boots": Charm(
        id="boots",
        label="star boots",
        phrase="star boots with quiet soles",
        helps={"slip"},
        required_factor="rhyme",
        prep="lace up the star boots first",
        tail="stepped along in the star boots without a single skid",
    ),
    "basket": Charm(
        id="basket",
        label="a woven basket",
        phrase="a woven basket with a soft lining",
        helps={"crack", "thorns"},
        required_factor="rhyme",
        prep="take a woven basket",
        tail="carried the prize safely in the woven basket",
    ),
}

HEROES = {
    "girl": ["Mira", "Luna", "Ayla", "Rose", "Elsa"],
    "boy": ["Finn", "Theo", "Eli", "Milo", "Jasper"],
}

TRAITS = ["kind", "brave", "curious", "gentle", "bright"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def quest_at_risk(quest: Quest) -> bool:
    return quest.danger in {"thorns", "slip", "crack"}


def select_charm(quest: Quest) -> Optional[Charm]:
    for charm in CHARMS.values():
        if quest.danger in charm.helps:
            return charm
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for qid, q in QUESTS.items():
            if not quest_at_risk(q):
                continue
            if select_charm(q) is not None:
                out.append((s, qid, select_charm(q).id))
    return out


# ---------------------------------------------------------------------------
# Fairy-tale narrative machinery
# ---------------------------------------------------------------------------

def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def introduce(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    world.say(
        f"Once upon a time, in {world.setting.place}, there lived a little {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} was {hero.memes.get('trait', 'kind')} and loved a good story."
    )
    world.say(
        f"One day, {hero.id} heard of a {quest.noun} hidden near the old roses, and {helper.id} promised to help."
    )
    _add_meme(hero, "wonder", 1)
    _add_meme(hero, "hope", 1)


def foreshadow(world: World, quest: Quest) -> None:
    world.say(
        f"But there was a surprise in the air: {quest.risk}. "
        f"The old paths could hide a twist, and that was the important factor."
    )
    _add_meme(world.get("hero"), "worry", 1)


def speak_rhyme(world: World, hero: Entity, quest: Quest, charm: Charm) -> None:
    _add_meme(hero, "rhyme", 1)
    world.say(
        f"{hero.id} smiled and said a rhyme: “If the day may try to bite, "
        f"{charm.label} will make it right.”"
    )
    world.say(
        f"{hero.id}'s {charm.label} was the clever factor that could keep {quest.noun} safe."
    )


def take_charm(world: World, hero: Entity, charm: Charm) -> None:
    hero.carried_by = hero.id
    _add_meter(hero, charm.id, 1)
    world.say(f"{hero.id} chose {charm.phrase} and {charm.prep}.")


def attempt_quest(world: World, hero: Entity, quest: Quest, charm: Charm) -> None:
    _add_meme(hero, "courage", 1)
    world.say(
        f"Then {hero.id} went to {world.setting.place} to {quest.verb}. "
        f"The leaves held still as {quest.clue} led the way."
    )
    if quest.danger in charm.helps:
        world.say(
            f"When the sharp place appeared, {charm.label} did its job, and the risk could not spoil the day."
        )
        _add_meter(hero, "safe_progress", 1)
    else:
        raise StoryError("No charm in this world can safely answer that quest.")


def resolve(world: World, hero: Entity, quest: Quest, charm: Charm, helper: Entity) -> None:
    _add_meme(hero, "joy", 1)
    _add_meme(helper, "joy", 1)
    world.say(
        f"At last, {hero.id} found the {quest.noun}. It was bright and small and real, and it was enough to win the day."
    )
    world.say(
        f"{hero.id} and {helper.id} brought it home, and the tale could remain happy from that moment on."
    )
    world.say(
        f"With {charm.label} and the rhyme still warm in mind, {hero.id} stayed brave, and the little victory remained."
    )


# ---------------------------------------------------------------------------
# World runner
# ---------------------------------------------------------------------------

def build_world(setting: Setting, quest: Quest, hero_name: str, hero_type: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="queen", label=helper_name))
    hero.id = hero_name
    helper.id = helper_name
    hero.type = hero_type
    helper.type = "queen"
    hero.memes["trait"] = trait

    world.current_quest = quest
    charm = select_charm(quest)
    if charm is None:
        raise StoryError("This quest has no fair and fitting charm.")
    world.current_charm = charm

    introduce(world, hero, helper, quest)
    world.para()
    foreshadow(world, quest)
    speak_rhyme(world, hero, quest, charm)
    take_charm(world, hero, charm)
    world.para()
    attempt_quest(world, hero, quest, charm)
    resolve(world, hero, quest, charm, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        quest=quest,
        charm=charm,
        setting=setting,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    charm = f["charm"]
    return [
        f'Write a short fairy tale for a young child that includes the word "surprise" and the word "rhyme".',
        f"Tell a gentle story where {hero.id} tries to {quest.verb} and a clever {charm.label} helps them win.",
        f"Write a story where the important factor is a rhyme, and the ending lets the good thing remain.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    charm: Charm = f["charm"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What kind of child was {hero.id} in the fairy tale?",
            answer=f"{hero.id} was a {trait} little {hero.type} who wanted to do a brave thing and help the story end well.",
        ),
        QAItem(
            question=f"What surprise made {hero.id} careful during the quest?",
            answer=f"The surprise was that {quest.risk}. That is why {hero.id} needed to think before going ahead.",
        ),
        QAItem(
            question=f"What helped {hero.id} win without trouble?",
            answer=f"{charm.label} helped {hero.id} win. It fit the danger of the quest and kept the prize safe.",
        ),
        QAItem(
            question=f"Who went with {hero.id}?",
            answer=f"{helper.id} went with {hero.id}, and the two of them brought the treasure home together.",
        ),
        QAItem(
            question=f"How did the ending remain happy?",
            answer=f"The ending remained happy because {hero.id} used a fitting charm, followed the rhyme, and found the {quest.noun} safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of sounds in words, like when the ends of two words sound alike.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make a story exciting or new.",
        ),
        QAItem(
            question="What does it mean for something to remain?",
            answer="To remain means to stay the same or stay in place for a while.",
        ),
        QAItem(
            question="What does it mean to win?",
            answer="To win means to succeed at something or get a good outcome after trying hard.",
        ),
        QAItem(
            question="What is a factor?",
            answer="A factor is something that helps make a result happen or helps explain why something turned out that way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is risky if it has a tangible danger.
quest_at_risk(Q) :- danger(Q, D), danger_kind(D).

% A charm is compatible when it helps with the quest's danger.
has_fix(Q, C) :- quest_at_risk(Q), charm(C), danger(Q, D), helps(C, D).

valid_story(S, Q, C) :- setting(S), quest(Q), charm(C), has_fix(Q, C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("danger", qid, quest.danger))
        lines.append(asp.fact("danger_kind", quest.danger))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for d in sorted(charm.helps):
            lines.append(asp.fact("helps", cid, d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show has_fix/2."))
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for c in CHARMS:
                if (s, q, c) in [tuple(x) for x in asp.atoms(model, "valid_story")]:
                    combos.append((s, q, c))
    return sorted(set(combos))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    charm: str
    name: str
    helper: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld with Surprise, Rhyme, and a winning factor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.charm:
        combos = [c for c in combos if c[2] == args.charm]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, charm = rng.choice(combos)
    q = QUESTS[quest]
    c = CHARMS[charm]
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(HEROES[gender])
    helper = args.helper or rng.choice(["Queen Mira", "Queen Elin", "Queen Sera"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, charm=charm, name=name, helper=helper, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(SETTINGS[params.place], QUESTS[params.quest], params.name, params.gender, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="castle", quest="rose", charm="cloak", name="Mira", helper="Queen Elin", gender="girl", trait="brave"),
    StoryParams(place="forest", quest="crown", charm="boots", name="Finn", helper="Queen Sera", gender="boy", trait="curious"),
    StoryParams(place="tower", quest="egg", charm="basket", name="Luna", helper="Queen Mira", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible stories ({len(stories)} shown by ASP):\n")
        for s, q, c in triples:
            print(f"  {s:8} {q:8} {c:8}")
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
