#!/usr/bin/env python3
"""
storyworlds/worlds/arrogant_affair_protective_magic_rhyme_superhero_story.py
=============================================================================

A tiny superhero storyworld about an arrogant hero, a tricky affair with a
villain, and a protective Magic Rhyme that turns the ending around.

Premise:
- A proud little superhero loves showing off.
- A nearby troublemaker starts an affair with danger: stealing, boasting,
  and stirring up a public mess.
- The hero rushes in with strength alone, but that makes the trouble worse.
- A mentor offers a protective Magic Rhyme, and the hero wins by using it
  instead of pride.

This world is intentionally small and constraint-checked: the protective magic
only makes sense when the villain's noisy spell can actually be blocked by a
rhyming shield. The story changes through simulated state, not just swapped
nouns.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "spark": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "courage": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    name: str
    indoor: bool = False
    supports: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    name: str
    act: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Charm:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    rhyme: str
    tail: str
    prep: str


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.threat: Optional[Threat] = None
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.threat = copy.deepcopy(self.threat)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    if not world.threat:
        return out
    for actor in world.chars():
        if actor.meters["spark"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("damage", actor.id, item.id, world.threat.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} took the hit.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.chars():
        if actor.memes["pride"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        out.append(f"{actor.id} rushed in too proudly.")
    return out


CAUSAL_RULES = [
    Rule("damage", _r_damage),
    Rule("conflict", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def threat_at_risk(threat: Threat, artifact: Artifact) -> bool:
    return artifact.region in threat.zone


def select_charm(threat: Threat, artifact: Artifact) -> Optional[Charm]:
    for c in CHARMS:
        if threat.mess in c.guards and artifact.region in c.covers:
            return c
    return None


def predict_damage(world: World, actor: Entity, threat: Threat, artifact_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), threat, narrate=False)
    art = sim.entities.get(artifact_id)
    return {"damaged": bool(art and art.meters["damage"] >= THRESHOLD)}


def _do_action(world: World, actor: Entity, threat: Threat, narrate: bool = True) -> None:
    world.zone = set(threat.zone)
    actor.meters["spark"] += 1
    actor.memes["pride"] += 1
    world.threat = threat
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} superhero who loved being admired.")


def love_city(world: World, hero: Entity) -> None:
    hero.memes["courage"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {world.city.name} and the bright roofs below.")


def buy_artifact(world: World, mentor: Entity, hero: Entity, art: Entity) -> None:
    world.say(f"One day, {mentor.id} gave {hero.id} {hero.pronoun('object')} {art.phrase}.")


def adore_artifact(world: World, hero: Entity, art: Entity) -> None:
    hero.memes["pride"] += 1
    art.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {art.label} and wore {art.it()} everywhere.")


def arrive(world: World, hero: Entity, mentor: Entity, threat: Threat) -> None:
    world.say(f"One afternoon, {hero.id} and {mentor.id} reached the {world.city.name} plaza.")
    world.say(f"There, a troublemaker tried to {threat.act}.")


def warn(world: World, mentor: Entity, hero: Entity, threat: Threat, art: Entity) -> bool:
    pred = predict_damage(world, hero, threat, art.id)
    if not pred["damaged"]:
        return False
    world.facts["predicted_damage"] = True
    world.say(f'"{art.label} could get ruined," {mentor.id} said. "A shielded plan will work better."')
    return True


def boast(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(f"{hero.id} grinned and said no one could beat {hero.pronoun('object')}.")
    world.say(f"{hero.pronoun().capitalize()} leaped toward the trouble at once.")


def scramble(world: World, hero: Entity, threat: Threat) -> None:
    hero.memes["spark"] += 1
    _do_action(world, hero, threat)
    world.say(f"The air flashed with noise, and the mess spread fast.")


def offer_charm(world: World, mentor: Entity, hero: Entity, threat: Threat, art: Entity) -> Optional[Charm]:
    charm = select_charm(threat, art)
    if charm is None:
        return None
    if predict_damage(world, hero, threat, art.id)["damaged"]:
        shield = world.add(Entity(
            id=charm.id,
            type="thing",
            label=charm.label,
            phrase=charm.label,
            owner=hero.id,
            protective=True,
            covers=set(charm.covers),
        ))
        shield.worn_by = hero.id
        world.say(f'{mentor.id} smiled. "{charm.prep}," {mentor.id} said, "and try the Magic Rhyme."')
        world.say(f'{mentor.id} taught {hero.id} a {charm.label}: "{charm.rhyme}"')
        return charm
    return None


def accept_charm(world: World, hero: Entity, mentor: Entity, threat: Threat, art: Entity, charm: Charm) -> None:
    hero.memes["pride"] = 0.0
    hero.memes["courage"] += 1
    world.say(f'{hero.id} nodded, listened, and whispered the Rhyme.')
    world.say(f'{charm.tail}. The trouble bounced away, and {art.label} stayed safe.')
    world.say(f'{hero.id} stood taller for a new reason: not because {hero.pronoun()} boasted, but because {hero.pronoun()} helped.')


def tell(city: City, threat: Threat, artifact: Artifact, hero_name: str = "Nova",
         hero_type: str = "girl", parent_type: str = "mentor", trait: str = "brilliant") -> World:
    world = World(city)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "arrogant"]))
    mentor = world.add(Entity(id="Mentor", kind="character", type=parent_type, label="the mentor"))
    art = world.add(Entity(
        id="art",
        type="thing",
        label=artifact.label,
        phrase=artifact.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        region=artifact.region,
        plural=artifact.plural,
    ))
    intro(world, hero)
    love_city(world, hero)
    buy_artifact(world, mentor, hero, art)
    adore_artifact(world, hero, art)
    world.para()
    arrive(world, hero, mentor, threat)
    warn(world, mentor, hero, threat, art)
    boast(world, hero)
    scramble(world, hero, threat)
    world.para()
    charm = offer_charm(world, mentor, hero, threat, art)
    if charm:
        accept_charm(world, hero, mentor, threat, art, charm)
    world.facts.update(hero=hero, mentor=mentor, art=art, threat=threat, charm=charm, city=city)
    return world


CITIES = {
    "sunport": City(name="Sunport Plaza", supports={"burst", "glow"}),
    "harbor": City(name="Harbor Square", supports={"splash", "burst"}),
    "library": City(name="Moonbeam Library", indoor=True, supports={"echo", "glow"}),
}

THREATS = {
    "boom": Threat(id="boom", name="Boom Bandit", act="blast bright sparks everywhere", mess="spark", zone={"torso"}, keyword="boom", tags={"spark", "hero"}),
    "glow": Threat(id="glow", name="Glow Goblin", act="smear glowing dust on capes", mess="spark", zone={"torso", "hands"}, keyword="glow", tags={"spark", "magic"}),
    "echo": Threat(id="echo", name="Echo Eel", act="shout loud rhymes at everyone", mess="spark", zone={"head", "torso"}, keyword="rhyme", tags={"rhyme", "magic"}),
}

ARTIFACTS = {
    "cape": Artifact(id="cape", label="a red cape", phrase="a red cape with a shiny clasp", region="torso"),
    "mask": Artifact(id="mask", label="a silver mask", phrase="a silver mask that glittered in the light", region="head"),
    "boots": Artifact(id="boots", label="blue boots", phrase="blue boots with starry toes", region="feet", plural=True),
}

CHARMS = [
    Charm(id="shieldrhyme", label="protective rhyme-armor", guards={"spark"}, covers={"torso"}, rhyme="If sparks leap and lights bounce high, my rhyming shield will catch the sky!", tail="The rhyme wrapped around the cape like a warm, bright blanket", prep="Put the cape under my shield first"),
    Charm(id="masksong", label="protective rhyme-song", guards={"spark"}, covers={"head"}, rhyme="With a soft and steady singing sound, the bright wild sparks will spin around!", tail="The rhyme twinkled over the mask like a cool little lantern", prep="Hold the mask steady while I sing"),
    Charm(id="bootchant", label="protective rhyme-chant", guards={"spark"}, covers={"feet"}, rhyme="Boots stay safe when magic rings, because a careful rhyme has wings!", tail="The rhyme sealed the boots with a neat, quiet glow", prep="Tap the boots to begin the chant"),
]

NAMES = ["Nova", "Iris", "Zane", "Milo", "Poppy", "Rex", "Luna", "Bea"]
TRAITS = ["brilliant", "bold", "quick", "cheerful", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for city_id, city in CITIES.items():
        for threat_id in city.supports:
            for art_id, art in ARTIFACTS.items():
                if threat_at_risk(THREATS[threat_id], art) and select_charm(THREATS[threat_id], art):
                    combos.append((city_id, threat_id, art_id))
    return combos


@dataclass
class StoryParams:
    city: str
    threat: str
    artifact: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "magic": [("What is magic?", "Magic is a pretend kind of power in stories that can make surprising things happen." আন)],
    "rhyme": [("What is a rhyme?", "A rhyme is a pair of words or sounds that end in a similar way, like cat and hat.")],
    "cape": [("What is a cape for?", "A cape is a piece of clothing worn over the shoulders to make a hero look dramatic.")],
    "mask": [("Why do heroes wear masks?", "Heroes sometimes wear masks to hide their faces and keep their secret identities safe.")],
    "boots": [("What are boots for?", "Boots cover your feet and help keep them safe, dry, or clean.")],
    "spark": [("What is a spark?", "A spark is a tiny flash of fire or light that can pop out quickly.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes the words "arrogant", "affair", and "protective".',
        f"Tell a gentle story about {f['hero'].id}, a little superhero who starts out arrogant but learns a protective Magic Rhyme from {f['mentor'].id}.",
        f"Write a story where a villainous affair with danger threatens {f['art'].label}, and a rhyme saves the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, art, threat = f["hero"], f["mentor"], f["art"], f["threat"]
    charm = f["charm"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {hero.type} superhero named {hero.id} who started out arrogant and then learned to be careful.",
        ),
        QAItem(
            question=f"What trouble started the affair with danger in the plaza?",
            answer=f"The troublemaker {threat.name} tried to {threat.act}, which made the plaza noisy and risky.",
        ),
        QAItem(
            question=f"What precious thing did {hero.id} want to protect?",
            answer=f"{hero.id} wanted to protect {art.phrase} from the wild mess caused by {threat.name}.",
        ),
    ]
    if charm:
        qa.append(QAItem(
            question="What was the protective Magic Rhyme for?",
            answer=f"It was for shielding {art.label} from {threat.mess}. The rhyme worked because it covered the right part of the hero's gear.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"At first {hero.id} acted arrogant and rushed in, but by the end {hero.id} listened, used the Magic Rhyme, and saved the day with help.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["threat"].tags)
    if world.facts.get("charm"):
        tags.add("magic")
        tags.add("rhyme")
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(city="sunport", threat="boom", artifact="cape", name="Nova", gender="girl", trait="brilliant"),
    StoryParams(city="library", threat="echo", artifact="mask", name="Milo", gender="boy", trait="bold"),
    StoryParams(city="harbor", threat="glow", artifact="boots", name="Poppy", gender="girl", trait="cheerful"),
]


def explain_rejection(threat: Threat, art: Artifact) -> str:
    if not threat_at_risk(threat, art):
        return f"(No story: {threat.act} does not reach the {art.label}, so there is no honest protective problem to solve.)"
    return f"(No story: no charm in this world protects {art.label} from {threat.mess}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CITIES.items():
        lines.append(asp.fact("city", cid))
        if c.indoor:
            lines.append(asp.fact("indoor", cid))
        for s in sorted(c.supports):
            lines.append(asp.fact("supports", cid, s))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        for r in sorted(t.zone):
            lines.append(asp.fact("zones", tid, r))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("wears_on", aid, a.region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, g))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(T, A) :- zones(T, R), wears_on(A, R).
can_protect(C, T, A) :- charm(C), at_risk(T, A), mess_of(T, M), guards(C, M), covers(C, R), wears_on(A, R).
valid(City, T, A) :- city(City), supports(City, T), at_risk(T, A), can_protect(_, T, A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about arrogance, affair, and protective Magic Rhyme.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.threat and args.artifact:
        t, a = THREATS[args.threat], ARTIFACTS[args.artifact]
        if not (threat_at_risk(t, a) and select_charm(t, a)):
            raise StoryError(explain_rejection(t, a))
    combos = [c for c in valid_combos()
              if (args.city is None or c[0] == args.city)
              and (args.threat is None or c[1] == args.threat)
              and (args.artifact is None or c[2] == args.artifact)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    city, threat, artifact = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(city=city, threat=threat, artifact=artifact, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(CITIES[params.city], THREATS[params.threat], ARTIFACTS[params.artifact], params.name, params.gender, "mentor", params.trait)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (city, threat, artifact) combos:\n")
        for city, threat, artifact in triples:
            print(f"  {city:8} {threat:8} {artifact:8}")
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
            header = f"### {p.name}: {p.threat} at {p.city} ({p.artifact})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
