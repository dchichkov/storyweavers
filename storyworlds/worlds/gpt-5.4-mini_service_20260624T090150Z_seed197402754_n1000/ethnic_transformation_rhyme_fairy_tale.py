#!/usr/bin/env python3
"""
storyworlds/worlds/ethnic_transformation_rhyme_fairy_tale.py
=============================================================

A small fairy-tale story world about a gentle magical transformation,
where a child learns that a rhyme can turn fear into courage and plain things
into beautiful festival things.

Seed tale:
---
In a bright little village, a shy child named Lila found a plain shawl in a
wooden chest. It belonged to her grandmother and was stitched with colorful
patterns from their family traditions. Lila loved the shawl, but she felt too
small to wear it at the spring fair.

Then a moonlit fairy appeared and sang a rhyme. Each line of the rhyme made
something change: the shawl shimmered, the ribbons brightened, and Lila
herself felt braver. When she spoke the rhyme back, her plain clothes turned
into a lovely festival outfit. She walked to the fair smiling, and the whole
village cheered.

World model:
---
    transformation magic -> item.form, item.color, item.beauty increase
                              actor.memes["wonder"] += 1
    brave rhyme spoken     -> actor.memes["courage"] += 1
                              actor.memes["fear"] -= 1
    community applause     -> actor.memes["belonging"] += 1
                              actor.memes["joy"] += 1

Narrative instruments:
---
    fairy sings a rhyme     -> magical change begins
    child repeats rhyme     -> transformation completes
    new festival outfit     -> ending image proves change
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "woman"}
        male = {"boy", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Motif:
    id: str
    noun: str
    rhyme_word: str
    transformation: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    type: str
    wear_place: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    ethnic: bool = True


@dataclass
class Charm:
    id: str
    label: str
    rhyme_line: str
    final_line: str
    guards: set[str]
    transforms_to: str


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.motif: Optional[Motif] = None

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.motif = self.motif
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_bloom(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("sparkle", 0.0) < THRESHOLD:
            continue
        sig = ("bloom", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["beauty"] = ent.meters.get("beauty", 0.0) + 1
        ent.meters["color"] = ent.meters.get("color", 0.0) + 1
        out.append(f"{ent.label} began to shimmer with bright color.")
    return out


def _r_courage(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("fear", 0.0) >= THRESHOLD and hero.memes.get("heard_rhyme", 0.0) >= THRESHOLD:
            sig = ("courage", hero.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
            hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
            out.append(f"{hero.id} felt braver after hearing the rhyme.")
    return out


def _r_belonging(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("courage", 0.0) < THRESHOLD or hero.memes.get("applause", 0.0) < THRESHOLD:
            continue
        sig = ("belonging", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["belonging"] = hero.memes.get("belonging", 0.0) + 1
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        out.append(f"The village made {hero.id} feel warmly welcome.")
    return out


RULES = [
    Rule("bloom", _r_bloom),
    Rule("courage", _r_courage),
    Rule("belonging", _r_belonging),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    motif: str
    gift: str
    charm: str
    seed: Optional[int] = None


PLACES = {
    "village_square": "the village square",
    "lantern_garden": "the lantern garden",
    "old_bridge": "the old bridge",
    "fair_lane": "the fair lane",
}

MOTIFS = {
    "shawl": Motif(
        id="shawl",
        noun="shawl",
        rhyme_word="tall",
        transformation="began to glow like sunset thread",
        glow="golden",
        tags={"ethnic", "cloth", "family"},
    ),
    "ribbon": Motif(
        id="ribbon",
        noun="ribbon",
        rhyme_word="dawn",
        transformation="twisted into a bright festival ribbon",
        glow="red",
        tags={"ethnic", "festival"},
    ),
    "beads": Motif(
        id="beads",
        noun="beads",
        rhyme_word="gleam",
        transformation="sparkled like little stars on a string",
        glow="blue",
        tags={"ethnic", "beads"},
    ),
}

GIFTS = {
    "shawl": Gift("shawl", "a woven shawl", "a woven shawl with family patterns", "shawl", "shoulders"),
    "vest": Gift("vest", "a festival vest", "a festival vest with bright trim", "vest", "torso"),
    "skirt": Gift("skirt", "a dancing skirt", "a dancing skirt with stitched flowers", "skirt", "legs", {"girl"}),
}

CHARMS = {
    "moon_rhyme": Charm(
        id="moon_rhyme",
        label="moon rhyme",
        rhyme_line="Moon above, please softly gleam,",
        final_line="Let this plain thing wake and beam!",
        guards={"fear"},
        transforms_to="festival_outfit",
    ),
    "river_rhyme": Charm(
        id="river_rhyme",
        label="river rhyme",
        rhyme_line="River bright and river low,",
        final_line="Teach my feet a gentle glow!",
        guards={"shyness"},
        transforms_to="brave_steps",
    ),
}

GIRL_NAMES = ["Lila", "Nora", "Mina", "Asha", "Rina", "Suri"]
BOY_NAMES = ["Milo", "Arin", "Kiran", "Toma", "Ivo", "Dara"]
TRAITS = ["shy", "kind", "gentle", "curious", "dreamy", "careful"]


def select_combo(rng: random.Random) -> tuple[str, str, str]:
    return rng.choice(list(PLACES)), rng.choice(list(MOTIFS)), rng.choice(list(GIFTS))


def build_story(world: World, hero: Entity, parent: Entity, gift: Entity, motif: Motif, charm: Charm) -> None:
    world.say(
        f"{hero.id} was a little {hero.traits[0]} {hero.type} who loved quiet songs and bright cloth."
    )
    world.say(
        f"In {world.place}, {hero.id}'s {parent.label} kept {hero.pronoun('possessive')} {gift.label} in a chest, "
        f"and the stitches carried family memories."
    )
    world.para()
    world.say(
        f"On festival eve, {hero.id} held the {motif.noun} and whispered, "
        f'"{charm.rhyme_line} {charm.final_line}"'
    )
    hero.memes["heard_rhyme"] = hero.memes.get("heard_rhyme", 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    gift.meters["sparkle"] = gift.meters.get("sparkle", 0.0) + 1
    motif_line = (
        f"The {motif.noun} {motif.transformation}, and its {motif.glow} glow lit the air."
    )
    world.say(motif_line)
    propagate(world, narrate=True)
    world.para()
    hero.memes["applause"] = hero.memes.get("applause", 0.0) + 1
    world.say(
        f"{hero.id} spoke the rhyme again, and the chest grew warm as dawn."
    )
    gift.worn_by = hero.id
    gift.meters["sparkle"] = gift.meters.get("sparkle", 0.0) + 1
    gift.meters["beauty"] = gift.meters.get("beauty", 0.0) + 1
    propagate(world, narrate=True)
    world.say(
        f"At last, {hero.id} went to the fair in {hero.pronoun('possessive')} {gift.label}, "
        f"and everyone clapped because the old family pattern shone like a tiny crown."
    )
    hero.memes["applause"] += 1
    propagate(world, narrate=True)


def tell(place: str, name: str, gender: str, parent_label: str, trait: str, motif_id: str, gift_id: str, charm_id: str) -> World:
    world = World(PLACES[place])
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=[trait, "brave"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_label, label="grandmother"))
    gift_cfg = GIFTS[gift_id]
    gift = world.add(Entity(id="gift", type=gift_cfg.type, label=gift_cfg.label, phrase=gift_cfg.phrase, owner=hero.id))
    motif = MOTIFS[motif_id]
    charm = CHARMS[charm_id]
    world.motif = motif

    build_story(world, hero, parent, gift, motif, charm)
    world.facts.update(hero=hero, parent=parent, gift=gift, motif=motif, charm=charm, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    gift: Entity = f["gift"]
    motif: Motif = f["motif"]
    charm: Charm = f["charm"]
    return [
        f'Write a fairy tale for a little child about "{motif.noun}" and a magical rhyme.',
        f"Tell a gentle story where {hero.id} is shy about wearing {gift.phrase}, then becomes brave through a rhyme.",
        f"Write a short story in a fairy-tale style where an old family treasure changes with singing and ends at a festival.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    gift: Entity = f["gift"]
    motif: Motif = f["motif"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question=f"Who learned the rhyme in {world.place}?",
            answer=f"{hero.id} learned the rhyme in {world.place} with help from {parent.label}.",
        ),
        QAItem(
            question=f"What family treasure changed during the story?",
            answer=f"The {gift.label} changed first, and it became fit for the festival when the rhyme was spoken.",
        ),
        QAItem(
            question=f"What did the {motif.noun} do in the story?",
            answer=f"The {motif.noun} helped the magic begin by shining and making the air feel bright.",
        ),
        QAItem(
            question=f"Why was {hero.id} nervous at first?",
            answer=f"{hero.id} was nervous because the treasure felt too special to wear, and the child feared making a mistake.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} walking to the fair in a beautiful transformed outfit while the village clapped.",
        ),
    ]


KNOWLEDGE = {
    "ethnic": [
        (
            "What does ethnic mean?",
            "Ethnic means something connected to a group of people, their traditions, their language, their clothes, or their celebrations.",
        )
    ],
    "shawl": [
        (
            "What is a shawl?",
            "A shawl is a soft cloth you can wrap around your shoulders to keep warm or to dress up for a special day.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair of words or sounds that match, like a little song that helps a story feel magical.",
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is a change from one form into another, like a plain thing becoming bright and new.",
        )
    ],
    "festival": [
        (
            "What is a festival?",
            "A festival is a happy celebration with music, food, dancing, and people gathered together.",
        )
    ],
}

KNOWLEDGE_ORDER = ["ethnic", "shawl", "rhyme", "transformation", "festival"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["motif"].tags)
    tags.add("rhyme")
    tags.add("transformation")
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} worn_by={e.worn_by}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world of rhyme and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"], default="grandmother")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--motif", choices=MOTIFS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--charm", choices=CHARMS)
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
    place = args.place or rng.choice(list(PLACES))
    motif = args.motif or rng.choice(list(MOTIFS))
    gift = args.gift or rng.choice(list(GIFTS))
    charm = args.charm or rng.choice(list(CHARMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gift and gender not in GIFTS[gift].genders:
        raise StoryError("That gift does not fit the chosen child in this fairy tale.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, parent=args.parent, trait=trait, motif=motif, gift=gift, charm=charm)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.name, params.gender, params.parent, params.trait, params.motif, params.gift, params.charm)
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


ASP_RULES = r"""
place(village_square).
place(lantern_garden).
place(old_bridge).
place(fair_lane).

motif(shawl).
motif(ribbon).
motif(beads).

gift(shawl).
gift(vest).
gift(skirt).

ethnic(shawl).
ethnic(ribbon).
ethnic(beads).

rhyme(moon_rhyme).
rhyme(river_rhyme).

transforms(shawl, festival_outfit).
transforms(vest, festival_outfit).
transforms(skirt, festival_outfit).

valid(Place, Motif, Gift, Charm) :- place(Place), motif(Motif), gift(Gift), rhyme(Charm), ethnic(Motif).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MOTIFS:
        lines.append(asp.fact("motif", m))
        lines.append(asp.fact("ethnic", m))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for c in CHARMS:
        lines.append(asp.fact("rhyme", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, m, g, c) for p in PLACES for m in MOTIFS for g in GIFTS for c in CHARMS]


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


CURATED = [
    StoryParams("village_square", "Lila", "girl", "grandmother", "shy", "shawl", "shawl", "moon_rhyme"),
    StoryParams("lantern_garden", "Milo", "boy", "grandmother", "curious", "ribbon", "vest", "river_rhyme"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
