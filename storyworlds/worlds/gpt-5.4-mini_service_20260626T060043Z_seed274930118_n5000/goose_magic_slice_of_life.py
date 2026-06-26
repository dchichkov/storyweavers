#!/usr/bin/env python3
"""
storyworlds/worlds/goose_magic_slice_of_life.py
================================================

A small slice-of-life storyworld about a goose, a little bit of magic,
and the everyday tug between wanting to play with something wonderful
and wanting to keep the home calm and tidy.

The premise is intentionally gentle: a goose discovers a useful magical
object or spell in a quiet neighborhood setting, tries it out, causes a
small everyday problem, and then helps solve it in a way that leaves the
scene a little brighter than before.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"goose"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"woman", "mother", "mom", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father", "dad", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    action: str
    effect: str
    mess: str
    zone: set[str]
    ward: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Charm:
    id: str
    label: str
    covers: set[str]
    wards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        w.zone = set(self.zone)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_mess(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for kind in ("sparkle", "wet"):
            if actor.meters.get(kind, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("mess", item.id, kind)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[kind] = item.meters.get(kind, 0) + 1
                item.meters["touched"] = item.meters.get("touched", 0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} picked up a little of the magic.")
    return out


def _r_tidying(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters.get("touched", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("tidy", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["work"] = carer.meters.get("work", 0) + 1
        out.append(f"That meant a little more tidying for {carer.label}.")
    return out


def _r_settle(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("flutter", 0) < THRESHOLD:
            continue
        if actor.memes.get("shared", 0) < THRESHOLD:
            continue
        sig = ("settle", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] = actor.memes.get("calm", 0) + 1
        out.append(f"The whole house felt calmer after that.")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("tidying", _r_tidying), Rule("settle", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def looks_at_risk(magic: Magic, gift: Gift) -> bool:
    return gift.region in magic.zone


def pick_charm(magic: Magic, gift: Gift) -> Optional[Charm]:
    for charm in CHARMS:
        if magic.mess in charm.wards and gift.region in charm.covers:
            return charm
    return None


def predict(world: World, actor: Entity, magic: Magic, gift_id: str) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get(actor.id), magic, narrate=False)
    gift = sim.entities.get(gift_id)
    return {"touched": bool(gift and gift.meters.get("touched", 0) >= THRESHOLD)}


def _do_magic(world: World, actor: Entity, magic: Magic, narrate: bool = True) -> None:
    if magic.id not in world.setting.affords:
        return
    world.zone = set(magic.zone)
    actor.meters[magic.mess] = actor.meters.get(magic.mess, 0) + 1
    actor.memes["flutter"] = actor.memes.get("flutter", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, goose: Entity) -> None:
    world.say(f"{goose.id} was a curious goose who liked quiet mornings and shiny surprises.")


def likes_magic(world: World, goose: Entity, magic: Magic) -> None:
    goose.memes["delight"] = goose.memes.get("delight", 0) + 1
    world.say(f"{goose.pronoun().capitalize()} loved the way {magic.phrase} made ordinary things feel special.")


def find(world: World, goose: Entity, gift: Entity, magic: Magic) -> None:
    world.say(f"One morning, {goose.id} found {goose.pronoun('possessive')} {gift.label} near {world.setting.place}.")
    world.say(f"Beside it was {magic.phrase}, waiting for somebody gentle enough to try it.")


def wants(world: World, goose: Entity, magic: Magic, gift: Entity) -> None:
    goose.memes["want"] = goose.memes.get("want", 0) + 1
    world.say(f"{goose.id} wanted to {magic.action} right away, but {goose.pronoun('possessive')} {gift.label} was close by.")


def warn(world: World, caretaker: Entity, goose: Entity, magic: Magic, gift: Entity) -> bool:
    pred = predict(world, goose, magic, gift.id)
    if not pred["touched"]:
        return False
    world.facts["predicted_effect"] = magic.effect
    world.say(f'"If you do that, your {gift.label} will get {magic.effect}," {caretaker.label} said.')
    return True


def playful(world: World, goose: Entity, magic: Magic) -> None:
    goose.memes["stubborn"] = goose.memes.get("stubborn", 0) + 1
    world.say(f"{goose.id} gave a soft honk and tried to {magic.action}.")
    _do_magic(world, goose, magic, narrate=True)


def worry(world: World, caretaker: Entity, goose: Entity, magic: Magic) -> None:
    goose.memes["shared"] = goose.memes.get("shared", 0) + 1
    world.say(f"{caretaker.label} reached out a hand and reminded {goose.pronoun('object')} to be careful.")
    world.say(f"Together they watched the magic drift across the room like a small bright breeze.")


def compromise(world: World, caretaker: Entity, goose: Entity, magic: Magic, gift: Entity) -> Optional[Charm]:
    charm = pick_charm(magic, gift)
    if charm is None:
        return None
    if predict(world, goose, magic, gift.id)["touched"]:
        return None
    obj = world.add(Entity(
        id=charm.id,
        type="charm",
        label=charm.label,
        owner=goose.id,
        caretaker=caretaker.id,
        protective=True,
        covers=set(charm.covers),
        plural=charm.plural,
    ))
    obj.worn_by = goose.id
    world.say(f"Then {caretaker.label} smiled and said, \"How about we {charm.prep}?\"")
    return charm


def accept(world: World, caretaker: Entity, goose: Entity, magic: Magic, gift: Entity, charm: Charm) -> None:
    goose.memes["calm"] = goose.memes.get("calm", 0) + 1
    goose.memes["delight"] = goose.memes.get("delight", 0) + 1
    world.say(f"{goose.id} blinked, then nodded, and {goose.pronoun()} followed along.")
    world.say(f"They {charm.tail}. Soon {goose.id} was {magic.action.replace('the ', '').replace('a ', '')}, and {gift.label} stayed neat and ready for the day.")


def tell(setting: Setting, magic: Magic, gift_cfg: Gift,
         goose_name: str = "Gus", caretaker_type: str = "mother") -> World:
    world = World(setting)
    goose = world.add(Entity(id=goose_name, kind="character", type="goose"))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, label="the neighbor"))
    gift = world.add(Entity(
        id="gift",
        type=gift_cfg.type,
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        owner=goose.id,
        caretaker=caretaker.id,
        region=gift_cfg.region,
        plural=gift_cfg.plural,
    ))

    introduce(world, goose)
    likes_magic(world, goose, magic)
    find(world, goose, gift, magic)
    world.para()
    wants(world, goose, magic, gift)
    warn(world, caretaker, goose, magic, gift)
    playful(world, goose, magic)
    worry(world, caretaker, goose, magic)
    world.para()
    charm = compromise(world, caretaker, goose, magic, gift)
    if charm:
        accept(world, caretaker, goose, magic, gift, charm)

    world.facts.update(goose=goose, caretaker=caretaker, gift=gift, magic=magic, charm=charm)
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"glow"}),
    "porch": Setting(place="the porch", indoor=False, affords={"sparkle"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"glow"}),
}

MAGICS = {
    "glow": Magic(
        id="glow",
        label="a glowing pebble",
        phrase="a glowing pebble",
        action="make the herb pots glow",
        effect="a little glittery",
        mess="sparkle",
        zone={"floor", "table"},
        ward="sparkle",
        keyword="magic",
        tags={"magic", "glow"},
    ),
    "sparkle": Magic(
        id="sparkle",
        label="a silver spoon spell",
        phrase="a tiny silver spoon spell",
        action="twirl the teacups with sparkles",
        effect="covered in sparkle",
        mess="sparkle",
        zone={"table", "apron"},
        ward="sparkle",
        keyword="magic",
        tags={"magic", "sparkle"},
    ),
}

GIFTS = {
    "scarf": Gift("scarf", "a soft striped scarf", "scarf", "neck"),
    "apron": Gift("apron", "a plain kitchen apron", "apron", "torso"),
    "hat": Gift("hat", "a little wool hat", "hat", "head"),
}

CHARMS = [
    Charm("cloth", "a dish towel", {"torso", "neck"}, {"sparkle"}, "put on a dish towel first", "got the dish towel", False),
    Charm("apron_cover", "a bigger apron", {"torso"}, {"sparkle"}, "use the bigger apron", "tied on the bigger apron", False),
    Charm("hood", "a soft hood", {"head"}, {"sparkle"}, "pull up the soft hood", "put on the soft hood", False),
]

GUS_NAMES = ["Gus", "Nora", "Pip", "Mabel"]
CURATED = [
    {"setting": "garden", "magic": "glow", "gift": "apron", "name": "Gus"},
    {"setting": "porch", "magic": "sparkle", "gift": "scarf", "name": "Nora"},
    {"setting": "kitchen", "magic": "glow", "gift": "hat", "name": "Pip"},
]


@dataclass
class StoryParams:
    setting: str
    magic: str
    gift: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for m, magic in MAGICS.items():
            if m not in setting.affords:
                continue
            for g, gift in GIFTS.items():
                if looks_at_risk(magic, gift) and pick_charm(magic, gift):
                    out.append((s, m, g))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    goose, magic, gift = f["goose"], f["magic"], f["gift"]
    return [
        f'Write a short slice-of-life story about a goose named {goose.id} and a bit of "{magic.keyword}" magic.',
        f"Tell a gentle story where {goose.id} wants to {magic.action} but a neighbor worries about {goose.pronoun('possessive')} {gift.label}.",
        f"Write a cozy story that includes a goose, an everyday object, and a small magical compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    goose, caretaker, gift, magic = f["goose"], f["caretaker"], f["gift"], f["magic"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {goose.id}, a curious goose who likes quiet magic and everyday things.",
        ),
        QAItem(
            question=f"What did {goose.id} want to do with the magic?",
            answer=f"{goose.id} wanted to {magic.action} because {goose.pronoun()} liked how it made the morning feel special.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} worry about the {gift.label}?",
            answer=f"{caretaker.label} worried that the {gift.label} would get {magic.effect} if the magic was used too close to it.",
        ),
    ]
    if f.get("charm"):
        charm = f["charm"]
        qa.append(QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {charm.label} first, which let {goose.id} enjoy the magic while the {gift.label} stayed safe.",
        ))
        qa.append(QAItem(
            question=f"How did {goose.id} feel at the end?",
            answer=f"{goose.id} felt calm and pleased, because the magic still happened and the little home stayed tidy.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    out.append(QAItem("What is a goose?", "A goose is a bird with a long neck that can walk, swim, and honk."לץ))
    out.append(QAItem("What is magic?", "Magic is something wonderful and unusual in stories that can make surprising things happen."))  # type: ignore
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(M, G) :- zone(M, R), region(G, R).
protects(C, M, G) :- charm(C), prize_at_risk(M, G), wards(C, W), mess(M, W), covers(C, R), region(G, R).
has_fix(M, G) :- protects(_, M, G).
valid(S, M, G) :- setting(S), affords(S, M), prize_at_risk(M, G), has_fix(M, G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s, setting in SETTINGS.items():
        lines.append(asp.fact("setting", s))
        if setting.indoor:
            lines.append(asp.fact("indoor", s))
        for m in sorted(setting.affords):
            lines.append(asp.fact("affords", s, m))
    for m, magic in MAGICS.items():
        lines.append(asp.fact("magic", m))
        lines.append(asp.fact("mess", m, magic.mess))
        for z in sorted(magic.zone):
            lines.append(asp.fact("zone", m, z))
    for g, gift in GIFTS.items():
        lines.append(asp.fact("gift", g))
        lines.append(asp.fact("region", g, gift.region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for w in sorted(c.wards):
            lines.append(asp.fact("wards", c.id, w))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about a goose and a little magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name", choices=GUS_NAMES)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.magic is None or c[1] == args.magic)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, m, g = rng.choice(sorted(combos))
    name = args.name or rng.choice(GUS_NAMES)
    return StoryParams(setting=s, magic=m, gift=g, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MAGICS[params.magic], GIFTS[params.gift], params.name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid_combos()
        print(f"{len(model)} compatible combos:")
        for s, m, g in model:
            print(f"  {s:7} {m:7} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for item in CURATED:
            params = StoryParams(**item)
            samples.append(generate(params))
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
