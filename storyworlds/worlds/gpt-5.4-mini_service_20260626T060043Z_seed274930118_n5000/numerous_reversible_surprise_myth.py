#!/usr/bin/env python3
"""
A standalone storyworld for a small mythic surprise tale with numerous,
reversible turns.

Premise:
- A childlike hero serves at a shrine.
- Many small offerings gather for a festival.
- A surprising blessing or omen appears.
- The surprise can be reversed by the right ritual action.
- The ending proves the world changed, then changed back in a careful way.

This file follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of shared results containers
- lazy import of asp in ASP helpers
- supports the required CLI modes
- emits a live world model, grounded story text, and QA pairs
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    sacred: bool = False
    reversible: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hill shrine"
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    verb: str
    gerund: str
    surprise: str
    reverse_verb: str
    reverse_result: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "altar"
    plural: bool = False


@dataclass
class Charm:
    id: str
    label: str
    prep: str
    tail: str
    reversible: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    rite: str
    prize: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "hill_shrine": Setting(place="the hill shrine", affords={"harvest", "bell"}),
    "river_temple": Setting(place="the river temple", affords={"harvest", "bell"}),
    "moon_grove": Setting(place="the moon grove", affords={"moon", "bell"}),
}

RITES = {
    "harvest": Rite(
        id="harvest",
        verb="scatter grain on the stone",
        gerund="scattering grain",
        surprise="the grain rose into a bright flock of sparks",
        reverse_verb="gather the grains back into the bowl",
        reverse_result="the sparks settled again as plain grain",
        kind="golden",
        tags={"grain", "spark", "many"},
    ),
    "bell": Rite(
        id="bell",
        verb="ring the bronze bell",
        gerund="ringing the bronze bell",
        surprise="the bell answered with a hidden voice from the dark water",
        reverse_verb="cover the bell mouth with the cloth",
        reverse_result="the hidden voice fell silent",
        kind="bronze",
        tags={"bell", "voice", "echo"},
    ),
    "moon": Rite(
        id="moon",
        verb="set out mooncakes for the night",
        gerund="setting out mooncakes",
        surprise="the moonlight touched every cake and made each one glow like a tiny shield",
        reverse_verb="turn the tray face down and bow",
        reverse_result="the glow sank back into the cakes",
        kind="silver",
        tags={"moon", "glow", "many"},
    ),
}

PRIZES = {
    "lanterns": Prize(
        label="lanterns",
        phrase="many paper lanterns",
        type="lanterns",
        region="shrine",
        plural=True,
    ),
    "bowls": Prize(
        label="bowls",
        phrase="numerous clay bowls",
        type="bowls",
        region="table",
        plural=True,
    ),
    "statue": Prize(
        label="statue",
        phrase="a small river statue",
        type="statue",
        region="altar",
    ),
}

CHARMS = {
    "rope": Charm(
        id="rope",
        label="a braided rope charm",
        prep="tie the rope around the bowl",
        tail="untied the rope charm and set the bowl right",
    ),
    "cloth": Charm(
        id="cloth",
        label="a white cloth",
        prep="cover the bell with the cloth",
        tail="folded the cloth back over the bell",
    ),
    "mirror": Charm(
        id="mirror",
        label="a polished mirror",
        prep="hold the mirror toward the moon",
        tail="turned the mirror away and let the moon rest",
    ),
}

HERO_NAMES = ["Lian", "Mira", "Sora", "Ari", "Niko", "Ira", "Tala", "Kai"]
HELPER_NAMES = ["Elder Reed", "Aunt Jun", "Brother Pine", "Sage Willow"]
TRAITS = ["gentle", "curious", "brave", "quiet", "devoted"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for rite_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, rite_id, prize_id))
    return combos


def prize_is_affected(rite: Rite, prize: Prize) -> bool:
    if rite.id == "harvest":
        return prize.plural
    if rite.id == "bell":
        return True
    if rite.id == "moon":
        return True
    return False


def select_charm(rite: Rite, prize: Prize) -> Optional[Charm]:
    if rite.id == "harvest" and prize.plural:
        return CHARMS["rope"]
    if rite.id == "bell":
        return CHARMS["cloth"]
    if rite.id == "moon":
        return CHARMS["mirror"]
    return None


def reasonableness_gate(rite: Rite, prize: Prize) -> bool:
    return prize_is_affected(rite, prize) and select_charm(rite, prize) is not None


def explain_rejection(rite: Rite, prize: Prize) -> str:
    return (
        f"(No story: {rite.gerund} does not make a believable mythic surprise with "
        f"{prize.phrase}, because there is no reversible charm that fits both the omen and the object.)"
    )


def _activate_surprise(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("rite", 0.0) < THRESHOLD:
            continue
        sig = ("surprise", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        rite_id = world.facts["rite"].id
        rite = RITES[rite_id]
        hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
        hero.memes["awe"] = hero.memes.get("awe", 0.0) + 1
        out.append(rite.surprise)
    return out


def _apply_reversal(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("reversed"):
        return out
    sig = ("reversed", world.facts["hero"].id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.facts["hero"]
    rite = world.facts["rite"]
    hero.memes["surprise"] = max(0.0, hero.memes.get("surprise", 0.0) - 1)
    out.append(rite.reverse_result)
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    produced.extend(_activate_surprise(world))
    produced.extend(_apply_reversal(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_surprise(world: World, hero: Entity, rite: Rite) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["rite"] = 1.0
    propagate(sim, narrate=False)
    return {
        "surprise": sim.get(hero.id).memes.get("surprise", 0.0) >= THRESHOLD,
        "awe": sim.get(hero.id).memes.get("awe", 0.0) >= THRESHOLD,
    }


def intro(world: World, hero: Entity, helper: Entity) -> None:
    trait = next((t for t in hero.meters.keys() if False), "")
    world.say(
        f"At {world.setting.place}, a little {hero.type} named {hero.id} served beside "
        f"{helper.id}, and the two of them kept the shrine bright with care."
    )


def many_offerings(world: World, prize: Entity) -> None:
    if prize.plural:
        world.say(
            f"Many hands had brought {prize.phrase}, and the whole place smelled of clean clay and lantern oil."
        )
    else:
        world.say(
            f"Only one treasured thing stood there: {prize.phrase}, placed where everyone could see it."
        )


def begin_rite(world: World, hero: Entity, rite: Rite, prize: Entity) -> None:
    hero.meters["rite"] = hero.meters.get("rite", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"During the festival, {hero.id} chose to {rite.verb}, because the old stories said that such a rite could wake sleeping luck."
    )
    propagate(world, narrate=True)


def witness_worry(world: World, helper: Entity, prize: Entity, rite: Rite) -> bool:
    pred = predict_surprise(world, world.facts["hero"], rite)
    if pred["surprise"]:
        world.say(
            f'"If you do that," {helper.id} said, "something unexpected may happen to {prize.it()}."'
        )
        return True
    return False


def react(world: World, hero: Entity, helper: Entity, rite: Rite) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say(
        f"{hero.id} paused, then looked again at the shining offering, wondering whether the old tale was waking."
    )


def offer_reversal(world: World, helper: Entity, hero: Entity, rite: Rite, prize: Entity) -> Optional[Charm]:
    charm = select_charm(rite, prize)
    if charm is None:
        return None
    world.say(
        f"{helper.id} smiled and held up {charm.label}. {helper.id} said, "
        f'"We can let the wonder happen, then {charm.prep} to return things to calm."'
    )
    return charm


def accept_reversal(world: World, hero: Entity, helper: Entity, rite: Rite, charm: Charm) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.facts["reversed"] = True
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} listened, followed the old way, and at last {charm.tail}. The shrine became quiet again, but it kept the memory of the wonder."
    )


def tell(setting: Setting, rite: Rite, prize_cfg: Prize, hero_name: str, hero_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, meters={}, memes={}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, meters={}, memes={}))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, plural=prize_cfg.plural))
    world.facts.update(hero=hero, helper=helper, prize=prize, rite=rite, charm=None, reversed=False)

    intro(world, hero, helper)
    world.para()
    many_offerings(world, prize)
    begin_rite(world, hero, rite, prize)
    world.para()
    if witness_worry(world, helper, prize, rite):
        react(world, hero, helper, rite)
    charm = offer_reversal(world, helper, hero, rite, prize)
    if charm:
        world.facts["charm"] = charm
        accept_reversal(world, hero, helper, rite, charm)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    rite = f["rite"]
    prize = f["prize"]
    return [
        f'Write a short mythic story for a young child about {hero.id}, {helper.id}, and a surprise at {world.setting.place}.',
        f"Tell a gentle myth where {hero.id} wants to {rite.verb}, but a wise helper fears what will happen to {prize.phrase}.",
        f'Write a story with the words "numerous" and "reversible" about an old shrine and a surprising rite.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    rite = f["rite"]
    prize = f["prize"]
    charm = f.get("charm")
    qa = [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {helper.id}, who kept watch over the shrine with care.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do during the festival?",
            answer=f"{hero.id} wanted to {rite.verb}. In the old story, that was the kind of action that could awaken a surprise.",
        ),
        QAItem(
            question=f"What was special about {prize.phrase}?",
            answer=f"There were {prize.phrase}, so the place felt full and important, like a gift meant for many people to share.",
        ),
    ]
    if world.facts.get("reversed"):
        qa.append(
            QAItem(
                question=f"How did the surprise end up being reversible?",
                answer=(
                    f"{helper.id} offered {charm.label} and showed how to use it after the wonder appeared. "
                    f"That let the story keep its awe, then return the shrine to calm without breaking the old rules."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shrine?",
            answer="A shrine is a special place where people leave offerings, pray quietly, and remember something sacred.",
        ),
        QAItem(
            question="What does numerous mean?",
            answer="Numerous means many. It is a word you can use when there are lots of things instead of just one or two.",
        ),
        QAItem(
            question="What does reversible mean?",
            answer="Reversible means something can be changed and then changed back again, so it does not stay altered forever.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a sudden change that the characters did not expect, like a strange sound or a light that appears at the right moment.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.plural:
            bits.append("plural=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill_shrine", rite="harvest", prize="lanterns", hero_name="Lian", hero_gender="girl", helper_name="Elder Reed", helper_gender="man"),
    StoryParams(place="river_temple", rite="bell", prize="statue", hero_name="Mira", hero_gender="girl", helper_name="Aunt Jun", helper_gender="woman"),
    StoryParams(place="moon_grove", rite="moon", prize="bowls", hero_name="Kai", hero_gender="boy", helper_name="Sage Willow", helper_gender="woman"),
]


KNOWLEDGE_ORDER = ["shrine", "numerous", "reversible", "surprise"]


def valid_story(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.rite in RITES and params.prize in PRIZES and reasonableness_gate(RITES[params.rite], PRIZES[params.prize])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rite and args.prize:
        rite = RITES[args.rite]
        prize = PRIZES[args.prize]
        if not reasonableness_gate(rite, prize):
            raise StoryError(explain_rejection(rite, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.rite is None or c[1] == args.rite)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, rite_id, prize_id = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    return StoryParams(place=place, rite=rite_id, prize=prize_id, hero_name=hero_name, hero_gender=hero_gender, helper_name=helper_name, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RITES[params.rite], PRIZES[params.prize], params.hero_name, params.hero_gender, params.helper_name, params.helper_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world with numerous, reversible surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


ASP_RULES = r"""
prize_at_risk(R, P) :- rite(R), prize(P), affects(R, P).
has_charm(R, P) :- prize_at_risk(R, P), charm(C), fits(C, R, P).
valid_story(Place, R, P) :- setting(Place), affords(Place, R), prize(P), has_charm(R, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for rite in sorted(s.affords):
            lines.append(asp.fact("affords", sid, rite))
    for rid, r in RITES.items():
        lines.append(asp.fact("rite", rid))
        for tag in sorted(r.tags):
            lines.append(asp.fact("affects", rid, "lanterns" if tag == "many" else rid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
    lines.append(asp.fact("fits", "rope", "harvest", "lanterns"))
    lines.append(asp.fact("fits", "cloth", "bell", "statue"))
    lines.append(asp.fact("fits", "mirror", "moon", "bowls"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, r, pr) for p, r, pr in valid_combos()}
    clingo_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            header = f"### {p.hero_name}: {p.rite} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
