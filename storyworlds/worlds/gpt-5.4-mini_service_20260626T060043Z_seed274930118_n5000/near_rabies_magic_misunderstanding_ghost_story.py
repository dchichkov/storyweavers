#!/usr/bin/env python3
"""
storyworlds/worlds/near_rabies_magic_misunderstanding_ghost_story.py
====================================================================

A small, child-facing ghost-story world built around a spooky misunderstanding:
a haunted house, a little bit of magic, and a fear that something "near rabies"
might be happening when it is actually just a strange, scary-looking creature
and a mistake in the dark.

The world is intentionally compact. It simulates:
- a small cast of typed entities,
- a few physical meters (distance, glowing, trembling, dampness),
- a few emotional memes (fear, courage, confusion, trust),
- one central misunderstanding that is resolved by looking closer,
- a gentle ghost-story mood with a safe ending.

The seed words "near" and "rabies" are carried in the domain vocabulary and
story prompt generation so the generated stories remain anchored to the seed.
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

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ghost-girl"}
        male = {"boy", "father", "man", "ghost-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    indoors: bool = True
    eerie: bool = True


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    type: str
    near: bool = False
    actually_rabid: bool = False
    scary_look: str = ""
    safe_truth: str = ""
    tag: str = "creature"


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    helps_with: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.distance: dict[str, float] = {}
        self.light: float = 0.0
        self.dark: float = 0.0

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.distance = dict(self.distance)
        clone.light = self.light
        clone.dark = self.dark
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "house": Setting(place="the old house", indoors=True, eerie=True),
    "attic": Setting(place="the attic", indoors=True, eerie=True),
    "yard": Setting(place="the misty yard", indoors=False, eerie=True),
}

CHARACTER_TRAITS = ["curious", "brave", "quiet", "gentle", "careful", "nervous"]
NAMES = ["Mina", "Theo", "Lia", "Jasper", "Nora", "Eli", "Pip", "Rose"]

CREATURES = {
    "stray": Creature(
        id="stray",
        label="a stray fox",
        phrase="a skinny fox with shining eyes",
        type="fox",
        near=True,
        actually_rabid=False,
        scary_look="its foam looked like moonlit bubbles in the dark",
        safe_truth="it was only hungry and frightened",
        tag="fox",
    ),
    "cat": Creature(
        id="cat",
        label="a black cat",
        phrase="a black cat with a bent tail",
        type="cat",
        near=True,
        actually_rabid=False,
        scary_look="its hunch made it look like a tiny shadow",
        safe_truth="it was only a cat sneaking through the hall",
        tag="cat",
    ),
    "bat": Creature(
        id="bat",
        label="a small bat",
        phrase="a small bat fluttering near the rafters",
        type="bat",
        near=False,
        actually_rabid=False,
        scary_look="its zigzag flight made it look like a ghost with wings",
        safe_truth="it was only looking for a quieter corner",
        tag="bat",
    ),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a warm gold flame",
        effect="light",
        helps_with={"dark", "fear"},
    ),
    "bell": Charm(
        id="bell",
        label="a silver bell",
        phrase="a silver bell tied to a blue ribbon",
        effect="notice",
        helps_with={"misunderstanding"},
    ),
    "chalk": Charm(
        id="chalk",
        label="chalk circles",
        phrase="a bit of white chalk for drawing safe circles",
        effect="boundary",
        helps_with={"near"},
    ),
}

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    creature: str
    charm: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------
def is_reasonable(setting: Setting, creature: Creature, charm: Charm) -> bool:
    # The story only makes sense if the creature is close enough to be mistaken
    # for something dangerous, but not actually rabid.
    if creature.actually_rabid:
        return False
    if setting.indoors and creature.id == "bat":
        return True
    if creature.near:
        return True
    return charm.id in {"lantern", "bell"}


def explain_rejection(creature: Creature) -> str:
    return (
        f"(No story: this world avoids actual rabies and instead uses a close "
        f"misunderstanding about {creature.label}. Try a non-rabid creature.)"
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def say_intro(world: World, hero: Entity, creature: Creature, charm: Charm) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} "
        f"{hero.type} who liked stories about ghosts and magic."
    )
    world.say(
        f"One damp evening, {hero.pronoun('subject')} carried {charm.phrase} "
        f"through {world.setting.place} and listened to every creak."
    )
    world.say(
        f"Near the doorway, there was {creature.phrase}. It looked spooky in the dark."
    )


def predict_misunderstanding(world: World, creature: Creature) -> dict:
    sim = world.copy()
    sim.dark = 1.0
    sim.light = 0.0
    sim.distance[creature.id] = 0.5 if creature.near else 2.0
    fear = 1.0
    confusion = 1.0 if creature.near else 0.5
    suspicious_label = "rabies" if creature.near else "ghost"
    return {
        "fear": fear,
        "confusion": confusion,
        "suspicious_label": suspicious_label,
        "close": creature.near,
    }


def raise_fear(world: World, hero: Entity, creature: Creature) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
    world.dark = 1.0
    world.say(
        f"{hero.id} froze. In the gloom, {creature.label} looked so odd that "
        f"{hero.pronoun('subject')} wondered if something dangerous was near."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} whispered the word 'rabies' by mistake, "
        f"because the shadows made every little thing sound scarier."
    )


def magic_to_look_closer(world: World, hero: Entity, charm: Charm, creature: Creature) -> None:
    if charm.id == "lantern":
        world.light = 1.0
        hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
        world.say(
            f"{hero.id} lifted {charm.label}, and the warm light pushed the dark back."
        )
    elif charm.id == "bell":
        hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
        world.say(
            f"{hero.id} gave {charm.label} a tiny ring, and the soft sound asked the room to listen."
        )
    else:
        world.say(
            f"{hero.id} drew chalk circles on the floor, making a safe little path to stand on."
        )
    world.say(
        f"With the spell of looking closer, {creature.label} no longer seemed like a warning."
    )


def reveal_truth(world: World, hero: Entity, creature: Creature) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    hero.memes["confusion"] = 0.0
    world.say(
        f"Then {hero.id} saw the truth: {creature.safe_truth}."
    )
    world.say(
        f"The scary shape had only been a misunderstanding in the dark."
    )


def resolve_gently(world: World, hero: Entity, creature: Creature) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    world.say(
        f"{hero.id} smiled, because the house felt less spooky once the mistake was gone."
    )
    if creature.tag == "fox":
        world.say(
            f"The fox slipped past the porch and into the mist, and {hero.id} waved instead of hiding."
        )
    elif creature.tag == "cat":
        world.say(
            f"The black cat blinked, hopped onto a stair, and disappeared like a soft shadow."
        )
    else:
        world.say(
            f"The little bat fluttered away, and its wings sounded like faraway paper."
        )
    world.say(
        f"By the end, the room was still haunted-looking, but {hero.id} knew better and felt safe."
    )


def tell(setting: Setting, creature: Creature, charm: Charm,
         hero_name: str, hero_type: str = "girl", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
    ))
    world.add(Entity(
        id=creature.id,
        type=creature.type,
        label=creature.label,
        phrase=creature.phrase,
        owner=None,
    ))
    world.add(Entity(
        id=charm.id,
        type="charm",
        label=charm.label,
        phrase=charm.phrase,
        owner=hero.id,
    ))

    say_intro(world, hero, creature, charm)
    world.para()
    raise_fear(world, hero, creature)
    world.say(
        f"{hero.id} remembered that magic could help when a scary thing was only a misunderstanding."
    )
    magic_to_look_closer(world, hero, charm, creature)
    reveal_truth(world, hero, creature)
    world.para()
    resolve_gently(world, hero, creature)

    world.facts = {
        "hero": hero,
        "creature": creature,
        "charm": charm,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    creature = f["creature"]
    charm = f["charm"]
    return [
        f'Write a short ghost story for children that includes the words "near" and "rabies" as part of a misunderstanding, not as a real illness.',
        f"Tell a gentle spooky story where {hero.id} uses {charm.label} to look closer at {creature.label} in the dark.",
        f"Write a magical misunderstanding story set in {world.setting.place} with a scary-looking creature and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    creature: Creature = f["creature"]
    charm: Charm = f["charm"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}.",
        ),
        QAItem(
            question=f"What did {hero.id} think at first when {creature.label} appeared near the door?",
            answer=f"{hero.id} got frightened and worried that something dangerous might be near, even saying 'rabies' by mistake because of the shadows.",
        ),
        QAItem(
            question=f"What magic thing helped {hero.id} look again?",
            answer=f"{charm.label} helped {hero.id} look closer, and its {charm.effect} made the dark less scary.",
        ),
        QAItem(
            question=f"What was the misunderstanding in the story?",
            answer=f"The misunderstanding was that {hero.id} thought the spooky-looking creature might be dangerous, but it was only {creature.safe_truth}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling safe and calm, after the truth came out and the creature slipped away without harm.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    creature: Creature = f["creature"]
    charm: Charm = f["charm"]
    out = [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something wrong at first and then learns the truth.",
        ),
        QAItem(
            question="What does a lantern do in the dark?",
            answer="A lantern gives off light so people can see shapes and places more clearly.",
        ),
        QAItem(
            question="Why can a scary shadow feel different after the light comes on?",
            answer="Light can show that a shadow is only a shape, not something dangerous.",
        ),
    ]
    if creature.tag == "fox":
        out.append(QAItem(
            question="What is a fox?",
            answer="A fox is a wild animal with a pointed face and a bushy tail.",
        ))
    if charm.id == "bell":
        out.append(QAItem(
            question="Why might a bell help people listen carefully?",
            answer="A bell can make a clear sound that gets attention and helps everyone pause and look again.",
        ))
    if charm.id == "chalk":
        out.append(QAItem(
            question="What can chalk be used for?",
            answer="Chalk can be used to draw lines, circles, or little signs on the ground.",
        ))
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
creature(C) :- creature_fact(C).
charm(H) :- charm_fact(H).
near_creature(C) :- creature_fact(C), near_fact(C).

misunderstanding(H,C) :- hero(H), creature_fact(C), near_fact(C), spooky_look(C).
safe_resolution(H,C) :- misunderstanding(H,C), charm_fact(H), helps_with(H,look_closer).
valid_story(S,C,H) :- setting_fact(S), hero(H), creature_fact(C), charm_fact(H), not_rabid(C), safe_resolution(H,C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature_fact", cid))
        if c.near:
            lines.append(asp.fact("near_fact", cid))
        if c.scary_look:
            lines.append(asp.fact("spooky_look", cid))
        if not c.actually_rabid:
            lines.append(asp.fact("not_rabid", cid))
    for chid, ch in CHARMS.items():
        lines.append(asp.fact("charm_fact", chid))
        for h in sorted(ch.helps_with):
            lines.append(asp.fact("helps_with", chid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    mapped = {(s, c, h) for (s, c, h) in cl}
    if py == mapped:
        print(f"OK: ASP and Python gates match ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("  python:", sorted(py))
    print("  asp:", sorted(mapped))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, creature in CREATURES.items():
            for chid, charm in CHARMS.items():
                if is_reasonable(setting, creature, charm):
                    combos.append((sid, cid, chid))
    return combos


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small ghost-story world with a magic misunderstanding."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=CHARACTER_TRAITS)
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
    setting_id = args.setting or rng.choice(list(SETTINGS))
    creature_id = args.creature or rng.choice(list(CREATURES))
    charm_id = args.charm or rng.choice(list(CHARMS))
    setting = SETTINGS[setting_id]
    creature = CREATURES[creature_id]
    charm = CHARMS[charm_id]

    if not is_reasonable(setting, creature, charm):
        raise StoryError(explain_rejection(creature))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(CHARACTER_TRAITS)
    return StoryParams(
        setting=setting_id,
        creature=creature_id,
        charm=charm_id,
        name=name,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    creature = CREATURES[params.creature]
    charm = CHARMS[params.charm]
    hero_type = "girl" if params.name in {"Mina", "Lia", "Nora", "Rose"} else "boy"
    world = tell(setting, creature, charm, params.name, hero_type, params.trait)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  light={world.light} dark={world.dark}")
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
    StoryParams(setting="house", creature="stray", charm="lantern", name="Mina", trait="curious"),
    StoryParams(setting="attic", creature="cat", charm="bell", name="Theo", trait="brave"),
    StoryParams(setting="yard", creature="bat", charm="chalk", name="Nora", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a}" for a in asp_valid_stories()))
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
            header = f"### {p.name}: {p.setting} / {p.creature} / {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
