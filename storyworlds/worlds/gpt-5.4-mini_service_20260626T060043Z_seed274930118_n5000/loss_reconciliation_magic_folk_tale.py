#!/usr/bin/env python3
"""
A standalone story world for a small folk tale about loss, magic, and
reconciliation.

Premise:
A child loses a treasured magical charm during a simple errand in a folk-tale
village. Fear and blame rise. A kind helper, spell, or wise elder helps the
child search, make amends, and mend the relationship.

The story is generated from a simulated world model with physical meters and
emotional memes. The turn comes from the loss, and the resolution comes from a
magic-assisted reconciliation that changes the world state.
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
    keeper: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "witch", "queen"}
        male = {"boy", "man", "father", "brother", "wizard", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    light: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Wish:
    id: str
    verb: str
    gerund: str
    loss_kind: str
    hurt: str
    clue: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    magic: bool = False
    plural: bool = False


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    glow: str
    heals: set[str] = field(default_factory=set)
    restores: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.path = list(self.path)
        return w


def _has(entity: Entity, key: str) -> bool:
    return entity.meters.get(key, 0.0) >= THRESHOLD or entity.memes.get(key, 0.0) >= THRESHOLD


def _loss(world: World) -> list[str]:
    out = []
    seeker = world.get(world.facts["seeker"])
    treasure = world.get(world.facts["treasure"])
    if seeker.meters.get("moved", 0.0) < THRESHOLD:
        return out
    sig = ("loss", seeker.id, treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.owner = None
    seeker.memes["fear"] = seeker.memes.get("fear", 0.0) + 1
    seeker.memes["grief"] = seeker.memes.get("grief", 0.0) + 1
    out.append(f"{seeker.pronoun('possessive').capitalize()} {treasure.label} was gone.")
    return out


def _blame(world: World) -> list[str]:
    out = []
    seeker = world.get(world.facts["seeker"])
    elder = world.get(world.facts["elder"])
    if seeker.memes.get("fear", 0.0) < THRESHOLD:
        return out
    sig = ("blame", seeker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["anger"] = seeker.memes.get("anger", 0.0) + 1
    elder.memes["concern"] = elder.memes.get("concern", 0.0) + 1
    out.append(f"{seeker.id} feared a scolding, and the air grew tight.")
    return out


def _magic_find(world: World) -> list[str]:
    out = []
    seeker = world.get(world.facts["seeker"])
    treasure = world.get(world.facts["treasure"])
    remedy = world.get(world.facts["remedy"])
    if seeker.memes.get("grief", 0.0) < THRESHOLD:
        return out
    sig = ("magic_find", treasure.id)
    if sig in world.fired:
        return out
    if remedy.carries != seeker.id:
        return out
    world.fired.add(sig)
    treasure.owner = seeker.id
    treasure.meters["found"] = 1.0
    seeker.memes["hope"] = seeker.memes.get("hope", 0.0) + 1
    out.append(f"{remedy.label} glowed softly and led them to {treasure.it()}.")
    return out


def _reconcile(world: World) -> list[str]:
    out = []
    seeker = world.get(world.facts["seeker"])
    elder = world.get(world.facts["elder"])
    treasure = world.get(world.facts["treasure"])
    if treasure.meters.get("found", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile", seeker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["anger"] = 0.0
    seeker.memes["joy"] = seeker.memes.get("joy", 0.0) + 1
    elder.memes["warmth"] = elder.memes.get("warmth", 0.0) + 1
    out.append(f"{seeker.id} and {elder.id} forgave one another, and the room felt wide again.")
    return out


def _restore(world: World) -> list[str]:
    out = []
    seeker = world.get(world.facts["seeker"])
    treasure = world.get(world.facts["treasure"])
    remedy = world.get(world.facts["remedy"])
    if seeker.memes.get("joy", 0.0) < THRESHOLD:
        return out
    sig = ("restore", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["glow"] = treasure.meters.get("glow", 0.0) + 1
    out.append(f"The {treasure.label} shone brighter after the apology.")
    return out


RULES = [_loss, _blame, _magic_find, _reconcile, _restore]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def tell(setting: Setting, wish: Wish, treasure_cfg: Treasure, remedy_cfg: Remedy,
         seeker_name: str, seeker_type: str, elder_type: str = "elder") -> World:
    world = World(setting)
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        label=seeker_name,
        meters={"moved": 1.0},
        memes={"hope": 0.0, "grief": 0.0, "fear": 0.0, "anger": 0.0, "joy": 0.0},
    ))
    elder = world.add(Entity(
        id="Aunt", kind="character", type=elder_type, label="Aunt Rowan",
        memes={"concern": 0.0, "warmth": 0.0},
    ))
    treasure = world.add(Entity(
        id="Treasure", kind="thing", type=treasure_cfg.type,
        label=treasure_cfg.label, phrase=treasure_cfg.phrase,
        owner=seeker.id, magical=treasure_cfg.magic,
        meters={"glow": 1.0 if treasure_cfg.magic else 0.0},
    ))
    remedy = world.add(Entity(
        id=remedy_cfg.id, kind="thing", type="spell", label=remedy_cfg.label,
        phrase=remedy_cfg.label, magical=True, carries=seeker.id,
    ))

    world.facts.update(
        seeker=seeker.id,
        elder=elder.id,
        treasure=treasure.id,
        remedy=remedy.id,
        wish=wish,
        setting=setting,
    )

    world.say(
        f"In {setting.place}, where {setting.light} drifted over the roofs, "
        f"{seeker.id} loved {wish.gerund} with {treasure.phrase} close at hand."
    )
    world.say(
        f"The little charm had a bright old magic, and {seeker.id} trusted it like a friend."
    )

    world.para()
    world.say(
        f"One day, {seeker.id} went to {setting.place} to {wish.verb}, but the path turned tricky."
    )
    world.say(
        f"When {seeker.id} reached into {seeker.pronoun('possessive')} pouch, the {treasure.label} was missing."
    )
    seeker.meters["moved"] += 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{elder.id} did not laugh. {elder.id} took a slow breath and lifted {remedy.label}."
    )
    world.say(
        f'"Sometimes lost things want to be found kindly," {elder.pronoun()} said.'
    )
    propagate(world, narrate=True)

    world.para()
    if treasure.owner == seeker.id:
        world.say(
            f"{seeker.id} apologized for snapping, and {elder.id} apologized for sounding stern."
        )
        world.say(
            f"Then they walked the lane together, and the magic led {seeker.pronoun('object')} back."
        )
        propagate(world, narrate=True)
    else:
        world.say("The magic did not answer, and the night stayed worried.")
    world.facts["resolved"] = treasure.owner == seeker.id
    return world


SETTINGS = {
    "village": Setting(place="the village green", light="warm lantern light", affords={"search"}),
    "wood": Setting(place="the whispering wood", light="silver moonlight", affords={"search"}),
    "cottage": Setting(place="the little cottage", light="golden hearthlight", affords={"search"}),
}

WISHES = {
    "search": Wish(
        id="search",
        verb="seek the hidden charm",
        gerund="searching under roots and stones",
        loss_kind="lost",
        hurt="worry",
        clue="a soft blue shimmer",
        keyword="loss",
        tags={"loss", "magic"},
    )
}

TREASURES = {
    "charm": Treasure(
        label="charm",
        phrase="a tiny silver charm with a moon scratched on it",
        type="charm",
        magic=True,
    ),
    "bell": Treasure(
        label="bell",
        phrase="a little bell that rang like dew",
        type="bell",
        magic=True,
    ),
    "stone": Treasure(
        label="stone",
        phrase="a smooth lucky stone",
        type="stone",
        magic=True,
    ),
}

REMEDIES = {
    "lantern": Remedy(
        id="lantern",
        label="a lantern-spell",
        action="shine",
        glow="soft",
        heals={"fear", "grief"},
        restores={"hope"},
    ),
    "thread": Remedy(
        id="thread",
        label="a silver thread charm",
        action="glimmer",
        glow="gentle",
        heals={"fear", "anger"},
        restores={"hope"},
    ),
    "song": Remedy(
        id="song",
        label="a humming song",
        action="ring",
        glow="warm",
        heals={"anger", "grief"},
        restores={"joy"},
    ),
}

NAMES = ["Mira", "Tobin", "Nell", "Bram", "Pia", "Ronan", "Sela", "Finn"]
TYPES = {"girl": ["girl"], "boy": ["boy"]}


@dataclass
class StoryParams:
    place: str
    wish: str
    treasure: str
    remedy: str
    name: str
    gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world about loss, magic, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def reasonableness(params: StoryParams) -> None:
    if params.gender not in TYPES:
        raise StoryError("invalid gender")
    if params.name and params.name not in NAMES:
        raise StoryError("unknown name")
    if params.treasure not in TREASURES:
        raise StoryError("unknown treasure")
    if params.remedy not in REMEDIES:
        raise StoryError("unknown remedy")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    wish = args.wish or "search"
    treasure = args.treasure or rng.choice(list(TREASURES))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    params = StoryParams(place=place, wish=wish, treasure=treasure, remedy=remedy, name=name, gender=gender)
    reasonableness(params)
    return params


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    treasure = world.get(f["treasure"])
    return [
        f'Write a short folk tale about a child named {seeker} who loses {treasure.phrase}.',
        f'Tell a gentle story about loss, magic, and reconciliation in {world.setting.place}.',
        f'Write a child-friendly tale where a magic helper leads {seeker} back to {treasure.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = world.get(f["seeker"])
    elder = world.get(f["elder"])
    treasure = world.get(f["treasure"])
    remedy = world.get(f["remedy"])
    resolved = f.get("resolved", False)
    items = [
        QAItem(
            question=f"What did {seeker.id} lose in the story?",
            answer=f"{seeker.id} lost {treasure.phrase}, and that made {seeker.pronoun('object')} feel afraid and sad.",
        ),
        QAItem(
            question=f"Who helped {seeker.id} after the loss?",
            answer=f"{elder.id} helped by staying calm and using {remedy.label} to search kindly.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The missing treasure was found again, and the hurt between them was softened by an apology.",
        ),
    ]
    if resolved:
        items.append(
            QAItem(
                question=f"How did the reconciliation happen for {seeker.id}?",
                answer=f"{seeker.id} apologized, {elder.id} answered kindly, and the magic led them back to {treasure.label}.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lantern-spell?",
            answer="A lantern-spell is a bit of magic that shines softly and helps people find things in the dark.",
        ),
        QAItem(
            question="Why can losing something feel so bad?",
            answer="Losing something can feel bad because you may worry it is gone forever and feel scared or sad until it is found.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset with each other and make peace again.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story with simple people, wonder, and a lesson or gift at the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} owner={e.owner} carries={e.carries} magical={e.magical}")
        if e.meters:
            out.append(f"  meters={e.meters}")
        if e.memes:
            out.append(f"  memes={e.memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
loss(seeker, treasure) :- moved(seeker), owns(seeker, treasure).
fear(seeker) :- loss(seeker, treasure).
blame(seeker) :- fear(seeker).
magic_finds(seeker, treasure) :- seek_help(seeker), carries(remedy, seeker).
reconcile(seeker, elder) :- magic_finds(seeker, treasure), apology(seeker), kindness(elder).
resolved(seeker, treasure) :- reconcile(seeker, elder).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for w in WISHES:
        lines.append(asp.fact("wish", w))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r))
    lines.append(asp.fact("owns", "seeker", "treasure"))
    lines.append(asp.fact("moved", "seeker"))
    lines.append(asp.fact("seek_help", "seeker"))
    lines.append(asp.fact("carries", "remedy", "seeker"))
    lines.append(asp.fact("apology", "seeker"))
    lines.append(asp.fact("kindness", "elder"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/2."))
    asp_atoms = set(asp.atoms(model, "resolved"))
    py = {("seeker", "treasure")}
    if asp_atoms == py:
        print("OK: ASP and Python reasoning agree.")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(asp_atoms))
    print("PY :", sorted(py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], WISHES[params.wish], TREASURES[params.treasure], REMEDIES[params.remedy], params.name, params.gender)
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
    StoryParams(place="village", wish="search", treasure="charm", remedy="lantern", name="Mira", gender="girl"),
    StoryParams(place="wood", wish="search", treasure="bell", remedy="thread", name="Tobin", gender="boy"),
    StoryParams(place="cottage", wish="search", treasure="stone", remedy="song", name="Nell", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted(asp.atoms(model, "resolved")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
