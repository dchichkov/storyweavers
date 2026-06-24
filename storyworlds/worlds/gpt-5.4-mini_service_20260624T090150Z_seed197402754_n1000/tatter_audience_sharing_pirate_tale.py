#!/usr/bin/env python3
"""
A small pirate-tale storyworld about sharing a tattered treasure clue with an audience.

Premise:
- A young pirate has a prized tattered chart or keepsake.
- A crowd or audience wants to see it, but the page is fragile or the ink is hard to read.
- The pirate must decide whether to hoard it, hide it, or share it carefully.

Turn:
- The audience cannot all crowd the treasure at once.
- A thoughtful sharing method is needed: hold it flat, take turns, or read it aloud.

Resolution:
- The pirate shares the tatter with care, and the audience learns something valuable.
- The ending image proves the item stayed safe and the crew felt richer together.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"damage": 0.0, "attention": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "greed": 0.0, "care": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sailor-woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "sailor-man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the deck of a tiny ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    danger: str
    region: str
    sharing: str
    audience_word: str = "audience"
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class CrewAid:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["greed"] < THRESHOLD:
            continue
        for art in [e for e in world.entities.values() if e.kind == "artifact"]:
            sig = ("damage", ent.id, art.id)
            if sig in world.fired:
                continue
            if art.meters["attention"] >= THRESHOLD:
                world.fired.add(sig)
                art.meters["damage"] += 1
                out.append(f"The {art.label} looked more frayed from too much grasping.")
    return out


CAUSAL_RULES = [_r_damage]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_begin(hero: Entity, audience: Entity, art: Artifact, setting: Setting) -> str:
    return (
        f"{hero.id} was a little pirate with a sharp eye and a brave grin. "
        f"{hero.pronoun().capitalize()} kept {hero.pronoun('possessive')} {art.label} close, "
        f"because it was {art.phrase}. "
        f"At {setting.place}, the {audience.label} had gathered to see what the crew had found."
    )


def tell(setting: Setting, art_cfg: Artifact, aid_cfg: CrewAid,
         hero_name: str = "Pip", hero_type: str = "boy") -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="pirate"))
    audience = world.add(Entity(id="Audience", kind="character", type="crowd", label="audience"))
    artifact = world.add(Entity(
        id="tatter",
        kind="artifact",
        type="tatter",
        label=art_cfg.label,
        phrase=art_cfg.phrase,
        owner=hero.id,
        caretaker=hero.id,
        plural=art_cfg.plural,
    ))
    aid = world.add(Entity(
        id=aid_cfg.id,
        kind="tool",
        type="tool",
        label=aid_cfg.label,
        plural=aid_cfg.plural,
    ))

    hero.memes["pride"] += 1
    audience.memes["joy"] += 1

    world.say(story_begin(hero, audience, art_cfg, setting))
    world.say(
        f"The crew loved the old {art_cfg.label}, but the page was so {art_cfg.danger} "
        f"that rough hands could ruin it."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to keep the {art_cfg.label} all to {hero.pronoun('object')}, "
        f"yet the {audience.label_word if hasattr(audience, 'label_word') else 'audience'} wanted to see."
    )
    world.say(
        f"{hero.pronoun().capitalize()} noticed that the best way to {art_cfg.sharing} was to "
        f"share it without letting the crowd crowd it."
    )
    hero.memes["care"] += 1
    audience.meters["attention"] += 1

    world.para()
    world.say(
        f"So {hero.id} used {aid.label} to {aid_cfg.prep}, and the whole deck grew quiet."
    )
    if aid_cfg.protects:
        world.say(
            f"It helped keep the {art_cfg.label} safe while the crew took turns listening."
        )

    if art_cfg.region == "air":
        art_cfg.region = "hands"

    if art_cfg.sharing == "read aloud":
        world.say(
            f"{hero.id} read the worn words out loud, and the audience leaned in like a wave."
        )
    else:
        world.say(
            f"{hero.id} held the {art_cfg.label} flat, and the audience took turns peeking at the treasure."
        )

    propagate(world, narrate=True)

    world.para()
    hero.memes["joy"] += 1
    audience.memes["joy"] += 1
    artifact.meters["attention"] = 0.0
    world.say(
        f"In the end, the {art_cfg.label} stayed safe, the crowd learned the clue, "
        f"and {hero.id} smiled like a captain with a kinder kind of treasure."
    )
    world.say(
        f"The little ship sailed on with a shared secret, and the tattered page rustled "
        f"softly in {hero.pronoun('possessive')} hands."
    )

    world.facts.update(
        hero=hero,
        audience=audience,
        artifact=artifact,
        aid=aid,
        setting=setting,
        artifact_cfg=art_cfg,
        aid_cfg=aid_cfg,
    )
    return world


SETTINGS = {
    "deck": Setting(place="the deck of a tiny ship", affords={"share"}),
    "harbor": Setting(place="the harbor pier", affords={"share"}),
    "cabin": Setting(place="the captain's cabin", affords={"share"}),
}


ARTIFACTS = {
    "map": Artifact(
        id="map",
        label="tattered map",
        phrase="yellow, torn, and full of secret islands",
        danger="thin and easily creased",
        region="hands",
        sharing="show it to the crew",
        tags={"map", "tatter"},
    ),
    "letter": Artifact(
        id="letter",
        label="tattered letter",
        phrase="smudged and frayed at the corners",
        danger="fragile and hard to hold",
        region="hands",
        sharing="read it aloud",
        tags={"letter", "tatter"},
    ),
    "banner": Artifact(
        id="banner",
        label="tattered banner",
        phrase="patched with salt and sun",
        danger="loose and snag-prone",
        region="air",
        sharing="show it to the audience",
        tags={"banner", "tatter"},
    ),
}

AIDS = {
    "tray": CrewAid(
        id="tray",
        label="a wooden tray",
        prep="set it on a wooden tray",
        tail="slid the tray carefully from hand to hand",
        protects={"hands"},
    ),
    "rope": CrewAid(
        id="rope",
        label="a short rope line",
        prep="hang it from a short rope line",
        tail="kept the crowd back from the edge",
        protects={"space"},
    ),
    "lantern": CrewAid(
        id="lantern",
        label="a lantern",
        prep="hold it near the page so all could see",
        tail="shined warm light on the worn words",
        protects={"eyes"},
    ),
}

NAMES = ["Pip", "Nell", "Jory", "Mira", "Tess", "Bo", "Kit", "Arlo"]
TRAITS = ["bold", "cheery", "curious", "nimble", "bright"]


@dataclass
class StoryParams:
    place: str
    artifact: str
    aid: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for art in ARTIFACTS:
            for aid in AIDS:
                if place in SETTINGS and art in ARTIFACTS and aid in AIDS:
                    out.append((place, art, aid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about sharing a tatter with an audience.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.artifact:
        combos = [c for c in combos if c[1] == args.artifact]
    if args.aid:
        combos = [c for c in combos if c[2] == args.aid]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, art, aid = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, artifact=art, aid=aid, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, art = f["hero"], f["artifact_cfg"]
    return [
        f'Write a short pirate tale for a young child about a {art.label} and an audience.',
        f"Tell a gentle story where {hero.id} decides how to share a {art.label} with the audience.",
        f'Write a story that includes the word "tatter" and ends with a shared treasure clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, audience, art, aid = f["hero"], f["audience"], f["artifact_cfg"], f["aid_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} share with the audience?",
            answer=f"{hero.id} shared the {art.label} carefully with the audience.",
        ),
        QAItem(
            question=f"Why did {hero.id} use {aid.label}?",
            answer=f"{hero.id} used {aid.label} to help share the {art.label} without ruining it.",
        ),
        QAItem(
            question=f"What made the {art.label} risky to pass around?",
            answer=f"It was {art.danger}, so rough handling could damage the tattered treasure.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tatter?",
            answer="A tatter is something worn, torn, or frayed, like an old page or flag that has been used a lot.",
        ),
        QAItem(
            question="Why is it kind to share with an audience?",
            answer="Sharing with an audience lets more people enjoy the same thing, and it can make everyone feel included.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
artifact_risky(A) :- artifact(A), fragile(A).
shared(A) :- artifact(A), aid(_).
good_story(P, A, I) :- setting(P), artifact(A), aid(I), artifact_risky(A), shared(A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ARTIFACTS.values():
        lines.append(asp.fact("artifact", a.id))
        lines.append(asp.fact("fragile", a.id))
    for i in AIDS.values():
        lines.append(asp.fact("aid", i.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ARTIFACTS[params.artifact], AIDS[params.aid], params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return

    if args.verify:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show good_story/3."))
        clingo_set = set(asp.atoms(model, "good_story"))
        python_set = set((p, a, i) for (p, a, i) in valid_combos())
        if clingo_set == python_set:
            print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
            return
        print("MISMATCH between clingo and valid_combos()")
        sys.exit(1)

    samples: list[StorySample] = []
    if args.all:
        for place, art, aid in valid_combos():
            params = StoryParams(place=place, artifact=art, aid=aid, name="Pip", gender="boy", trait="bold")
            samples.append(generate(params))
    else:
        seen = set()
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
