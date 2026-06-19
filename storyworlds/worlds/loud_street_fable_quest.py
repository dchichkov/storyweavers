#!/usr/bin/env python3
"""
storyworlds/worlds/loud_street_fable_quest.py
=============================================

A standalone story world for:

    Words: loud street
    Features: Quest
    Style: Fable

The domain is a small fable quest through a loud street. The hero must carry a
needed gift to a quiet place, but one kind of street noise blocks the quest. The
world refuses weak fixes: earmuffs do not calm a crowd, a bell sign does not
quiet barking, and a whispered request does not stop a rumbly cart. A compatible
story exists only when the offered aid actually addresses the loud obstacle.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "vixen", "hen"}
        male = {"boy", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Street:
    id: str
    place: str
    crowd: str
    crossing: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    treasure: str
    destination: str
    need: str
    lesson_good: str
    lesson_bad: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Noise:
    id: str
    label: str
    source: str
    sound: str
    blocks: str
    kind: str
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    handles: set[str]
    action: str
    result: str
    moral_word: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, street: Street) -> None:
        self.street = street
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.street)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise_blocks(world: World) -> list[str]:
    out: list[str] = []
    street = world.get("street")
    hero = world.get("hero")
    if street.meters["noise"] < THRESHOLD or hero.memes["quest"] < THRESHOLD:
        return out
    sig = ("blocked", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.meters["blocked"] += 1
    out.append("__blocked__")
    return out


def _r_aid_quiets(world: World) -> list[str]:
    out: list[str] = []
    street = world.get("street")
    aid = world.entities.get("aid")
    hero = world.get("hero")
    if not aid or aid.meters["used"] < THRESHOLD:
        return out
    sig = ("quieted", aid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    street.meters["noise"] = 0.0
    hero.meters["blocked"] = 0.0
    hero.memes["confidence"] += 1
    out.append("__quieted__")
    return out


def _r_quest_done(world: World) -> list[str]:
    hero = world.get("hero")
    gift = world.get("gift")
    if hero.meters["blocked"] >= THRESHOLD or gift.meters["delivered"] < THRESHOLD:
        return []
    sig = ("quest_done", gift.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["wisdom"] += 1
    hero.memes["joy"] += 1
    return ["__quest_done__"]


CAUSAL_RULES = [
    Rule("noise_blocks", "social", _r_noise_blocks),
    Rule("aid_quiets", "physical", _r_aid_quiets),
    Rule("quest_done", "quest", _r_quest_done),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def aid_fits(noise: Noise, aid: Aid) -> bool:
    return noise.kind in aid.handles


def street_supports(street: Street, noise: Noise) -> bool:
    return noise.id in street.affords


def select_aid(noise: Noise) -> Optional[Aid]:
    for aid in AIDS.values():
        if aid_fits(noise, aid):
            return aid
    return None


def predict_block(world: World, noise: Noise) -> dict:
    sim = world.copy()
    raise_noise(sim, noise, narrate=False)
    hero = sim.get("hero")
    street = sim.get("street")
    return {
        "blocked": hero.meters["blocked"] >= THRESHOLD,
        "noise": street.meters["noise"],
        "worry": hero.memes["worry"],
    }


def introduce(world: World, hero: Entity, elder: Entity, quest: Quest) -> None:
    trait = hero.traits[0] if hero.traits else "small"
    article = "an" if trait[:1].lower() in "aeiou" else "a"
    world.say(
        f"Once there was {article} {trait} {hero.type} named {hero.id}, who lived beside "
        f"{world.street.place}."
    )
    world.say(
        f"Every morning {elder.id}, the old {elder.type}, said, "
        f'"A small step with a steady heart can finish a great quest."'
    )
    hero.memes["quest"] += 1
    world.say(
        f"One day {elder.id} gave {hero.id} {quest.treasure} and asked "
        f"{hero.pronoun('object')} to carry it to {quest.destination}, because "
        f"{quest.need}."
    )


def enter_street(world: World, hero: Entity, noise: Noise) -> None:
    world.para()
    world.say(
        f"{hero.id} tucked the gift close and stepped onto the loud street. "
        f"{world.street.crowd.capitalize()} hurried by, and {world.street.crossing}."
    )
    world.say(f"Then {noise.source} made the street shake with {noise.sound}.")


def raise_noise(world: World, noise: Noise, narrate: bool = True) -> None:
    street = world.get("street")
    street.meters["noise"] += 1
    street.attrs["noise"] = noise.id
    propagate(world, narrate=narrate)


def warn(world: World, elder: Entity, hero: Entity, noise: Noise) -> None:
    pred = predict_block(world, noise)
    world.facts["predicted_block"] = pred["blocked"]
    world.facts["predicted_noise"] = pred["noise"]
    if pred["blocked"]:
        world.say(
            f'"Remember," called {elder.id}, "{noise.warning}; if you only rush, '
            f'the {noise.label} will swallow your quest."'
        )


def worried(world: World, hero: Entity, noise: Noise) -> None:
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id} tried to hurry, but {noise.blocks}. "
            f"{hero.pronoun().capitalize()} nearly turned back."
        )


def use_aid(world: World, hero: Entity, aid_def: Aid, noise: Noise) -> None:
    world.para()
    aid = world.add(Entity("aid", type="aid", label=aid_def.label, owner=hero.id))
    aid.meters["used"] += 1
    world.say(
        f"Then {hero.id} remembered the fable's rule: do not fight every loud "
        f"thing with more noise. {hero.pronoun().capitalize()} used {aid_def.label}: "
        f"{aid_def.action}."
    )
    propagate(world, narrate=False)
    if world.get("street").meters["noise"] < THRESHOLD:
        world.say(aid_def.result)
        world.facts["aid_worked"] = True
    else:
        world.say(f"But the {noise.label} stayed loud, and the quest could not go on.")
        world.facts["aid_worked"] = False


def deliver(world: World, hero: Entity, quest: Quest) -> None:
    gift = world.get("gift")
    if world.get("street").meters["noise"] >= THRESHOLD:
        return
    gift.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With the street quiet enough to think, {hero.id} crossed safely and "
        f"brought {quest.treasure} to {quest.destination}."
    )


def moral(world: World, hero: Entity, elder: Entity, quest: Quest, aid: Aid) -> None:
    if hero.memes["wisdom"] >= THRESHOLD:
        world.say(
            f"{elder.id} nodded. \"{quest.lesson_good}\" And from then on, "
            f"{hero.id} remembered that {aid.moral_word} can be braver than a shout."
        )


def tell(street: Street, quest: Quest, noise: Noise, aid_def: Aid,
         hero_name: str = "Nico", hero_type: str = "hare",
         elder_type: str = "tortoise", trait: str = "quick") -> World:
    world = World(street)
    hero = world.add(Entity("hero", kind="character", type=hero_type,
                            label=hero_name, traits=[trait], role="hero"))
    hero.id = hero_name
    world.entities["hero"] = hero
    elder = world.add(Entity("elder", kind="character", type=elder_type,
                             label="the elder", role="mentor"))
    elder.id = ELDER_NAMES[elder_type]
    world.entities["elder"] = elder
    street_ent = world.add(Entity("street", type="street", label=street.place))
    gift = world.add(Entity("gift", type="gift", label=quest.treasure, owner=hero.id))

    introduce(world, hero, elder, quest)
    enter_street(world, hero, noise)
    warn(world, elder, hero, noise)
    raise_noise(world, noise, narrate=False)
    worried(world, hero, noise)
    use_aid(world, hero, aid_def, noise)
    deliver(world, hero, quest)
    moral(world, hero, elder, quest, aid_def)

    world.facts.update(
        hero=hero, elder=elder, street=street, quest=quest, noise=noise,
        aid=aid_def, gift=gift,
        completed=gift.meters["delivered"] >= THRESHOLD,
        blocked_once=("blocked", hero.id) in world.fired,
    )
    return world


STREETS = {
    "market": Street(
        "market", "Cobbler Street", "market carts", "painted crosswalk stones winked in the dust",
        affords={"bells", "barkers", "drums"}),
    "school": Street(
        "school", "School Street", "children with lunch pails", "a line of chalk arrows pointed ahead",
        affords={"whistles", "drums", "carts"}),
    "harbor": Street(
        "harbor", "Harbor Street", "fish sellers and sailors", "ropes creaked over the crossing",
        affords={"bells", "carts", "barkers"}),
}

QUESTS = {
    "seed": Quest(
        "seed", "a silver seed", "the quiet garden", "the hungry birds needed shade",
        "A quest is not won by being louder than trouble, but by answering it wisely.",
        "Noise swallowed the seed's road.", tags={"seed", "quest", "fable"}),
    "letter": Quest(
        "letter", "a blue letter", "the little library", "the librarian needed news before sunset",
        "The right help turns a hard road into a path.",
        "Noise stole the letter's way.", tags={"letter", "quest", "fable"}),
    "loaf": Quest(
        "loaf", "a warm loaf", "the hill cottage", "Grandma Wren was waiting for supper",
        "Kindness travels best when patience leads it.",
        "Noise kept supper from the hill.", tags={"bread", "quest", "fable"}),
}

NOISES = {
    "bells": Noise(
        "bells", "bell clamor", "a wagon of cracked bells", "clang-clang-clang",
        "the clanging hid the crossing call", "ringing",
        "listen for the quiet beat under the clang", tags={"loud", "bells"}),
    "drums": Noise(
        "drums", "drum thunder", "a troop of drummers", "boom-boom-boom",
        "the booming shook the little gift", "rhythm",
        "match the beat before you cross it", tags={"loud", "drums"}),
    "barkers": Noise(
        "barkers", "barking crowd", "three shopkeepers calling at once", "buy, try, pie",
        "the shouting tangled the directions", "voices",
        "ask for one voice at a time", tags={"loud", "voices"}),
    "whistles": Noise(
        "whistles", "whistle shriek", "the crossing guard's stuck whistle", "tweet-tweet-tweet",
        "the shriek made every step feel sharp", "whistle",
        "soften a sharp sound before it scatters your courage", tags={"loud", "whistle"}),
    "carts": Noise(
        "carts", "cart rumble", "heavy stone carts", "rattle-rattle-rattle",
        "the rumble covered the hoofsteps in the road", "rumble",
        "wait for the wheels to slow", tags={"loud", "street"}),
}

AIDS = {
    "cloth": Aid(
        "cloth", "a folded cloth", {"ringing", "whistle"},
        "covered the loudest source and softened the sound",
        "The sharp sound sank into a small, polite hush.",
        "gentleness", tags={"sound", "quiet"}),
    "beat": Aid(
        "beat", "a steady tapping stick", {"rhythm", "rumble"},
        "tapped a slow pattern until the loud beat found a safer pace",
        "The noise settled into a walking rhythm.",
        "patience", tags={"rhythm", "quiet"}),
    "sign": Aid(
        "sign", "a painted quiet sign", {"voices"},
        "held up the sign and waited until each caller spoke one at a time",
        "The callers lowered their voices and made a lane through the crowd.",
        "courtesy", tags={"listening", "quiet"}),
}

ELDER_NAMES = {"tortoise": "Tessa", "owl": "Old Oren", "badger": "Bram"}
HEROES = {
    "hare": ["Nico", "Pip", "Milo", "Hattie"],
    "mouse": ["Mina", "Pip", "Nell", "Timo"],
    "sparrow": ["Sora", "Finn", "Pico", "Lina"],
}
TRAITS = ["quick", "small", "eager", "brave", "kind"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, street in STREETS.items():
        for qid in QUESTS:
            for nid, noise in NOISES.items():
                if not street_supports(street, noise):
                    continue
                aid = select_aid(noise)
                if aid:
                    combos.append((sid, qid, nid, aid.id))
    return combos


@dataclass
class StoryParams:
    street: str
    quest: str
    noise: str
    aid: str
    name: str
    hero: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "loud": [("What does loud mean?",
              "Loud means a sound is strong and easy to hear. Very loud sounds can make it hard to listen carefully.")],
    "street": [("Why should people be careful on a street?",
                "A street can have carts, bikes, or cars moving through it, so people should stop, look, and listen before crossing.")],
    "quest": [("What is a quest?",
               "A quest is a journey with an important goal. In fables, the journey often teaches a lesson.")],
    "fable": [("What is a fable?",
               "A fable is a short story that teaches a lesson, often with animal characters.")],
    "quiet": [("Why can quiet help someone think?",
               "Quiet gives your ears and mind room to notice small clues, so it is easier to make a good choice.")],
    "rhythm": [("What is a rhythm?",
                "A rhythm is a pattern of beats. Marching, clapping, and tapping can all make rhythms.")],
    "listening": [("Why is listening useful?",
                   "Listening helps people understand one another instead of adding more noise to a problem.")],
    "seed": [("What does a seed need to grow?",
              "A seed needs soil, water, sunlight, and time before it can grow into a plant.")],
    "bread": [("Why is warm bread carried carefully?",
               "Warm bread can be soft, so carrying it carefully keeps it from getting squashed or dirty.")],
    "letter": [("Why are letters delivered?",
                "Letters carry messages from one person to another, especially when the people are far apart.")],
}
KNOWLEDGE_ORDER = ["loud", "street", "quest", "fable", "quiet", "rhythm", "listening", "seed", "bread", "letter"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, noise = f["hero"], f["quest"], f["noise"]
    return [
        f'Write a fable for young children using the words "loud street" where {hero.id} goes on a quest with {quest.treasure}.',
        f"Tell a quest story where a {hero.type} must cross a loud street, learns not to answer {noise.label} with more noise, and finishes the errand wisely.",
        f'Write a short animal fable about patience, a noisy obstacle, and the lesson "{quest.lesson_good}"',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, elder, quest, noise, aid = f["hero"], f["elder"], f["quest"], f["noise"], f["aid"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a {hero.type}, and {elder.id}, the old {elder.type}."),
        (f"What quest did {hero.id} receive?",
         f"{elder.id} asked {hero.id} to carry {quest.treasure} to {quest.destination}. The gift mattered because {quest.need}."),
        ("What made the street hard to cross?",
         f"The street was loud because {noise.source} made {noise.sound}. That noise blocked the quest by making it hard for {hero.id} to think and cross safely."),
        (f"How did {hero.id} solve the problem?",
         f"{hero.id} used {aid.label}: {aid.action}. That matched the kind of noise, so the street became quiet enough for the quest to continue."),
        ("What lesson did the fable teach?",
         f"It taught that a quest is not won by making more noise. The right kind of help, used with patience, can be braver than shouting."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"loud", "street"} | set(f["quest"].tags) | set(f["noise"].tags) | set(f["aid"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("market", "seed", "bells", "cloth", "Nico", "hare", "tortoise", "quick"),
    StoryParams("school", "letter", "drums", "beat", "Mina", "mouse", "owl", "small"),
    StoryParams("harbor", "loaf", "barkers", "sign", "Sora", "sparrow", "badger", "kind"),
    StoryParams("school", "seed", "whistles", "cloth", "Pip", "mouse", "tortoise", "brave"),
    StoryParams("harbor", "letter", "carts", "beat", "Finn", "sparrow", "owl", "eager"),
]


def explain_rejection(street: Street, noise: Noise, aid: Optional[Aid] = None) -> str:
    if not street_supports(street, noise):
        return (f"(No story: {street.place} does not plausibly feature {noise.label}; "
                "the obstacle should belong to the street being crossed.)")
    if aid is not None and not aid_fits(noise, aid):
        return (f"(No story: {aid.label} does not answer {noise.label}. "
                f"It handles {sorted(aid.handles)}, but the obstacle is {noise.kind}.)")
    return f"(No story: no compatible aid in the catalog answers {noise.label}.)"


ASP_RULES = r"""
street_supports(S,N) :- affords(S,N).
aid_fits(N,A) :- noise_kind(N,K), handles(A,K).
has_aid(N,A) :- aid_fits(N,A).
valid(S,Q,N,A) :- street(S), quest(Q), noise(N), aid(A), street_supports(S,N), has_aid(N,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, street in STREETS.items():
        lines.append(asp.fact("street", sid))
        for nid in sorted(street.affords):
            lines.append(asp.fact("affords", sid, nid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for nid, noise in NOISES.items():
        lines.append(asp.fact("noise", nid))
        lines.append(asp.fact("noise_kind", nid, noise.kind))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for kind in sorted(aid.handles):
            lines.append(asp.fact("handles", aid_id, kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c_set, p_set = set(asp_valid_combos()), set(valid_combos())
    if c_set == p_set:
        print(f"OK: clingo gate matches valid_combos() ({len(c_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c_set - p_set:
        print("  only in clingo:", sorted(c_set - p_set))
    if p_set - c_set:
        print("  only in python:", sorted(p_set - c_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a loud street fable quest. Unspecified choices are random.")
    ap.add_argument("--street", choices=STREETS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP gate matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print facts + inline ASP rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.street and args.noise:
        st, nz = STREETS[args.street], NOISES[args.noise]
        if not street_supports(st, nz):
            raise StoryError(explain_rejection(st, nz))
    if args.noise and args.aid:
        nz, aid = NOISES[args.noise], AIDS[args.aid]
        if not aid_fits(nz, aid):
            street = STREETS[args.street] if args.street else next(iter(STREETS.values()))
            raise StoryError(explain_rejection(street, nz, aid))

    combos = [c for c in valid_combos()
              if (args.street is None or c[0] == args.street)
              and (args.quest is None or c[1] == args.quest)
              and (args.noise is None or c[2] == args.noise)
              and (args.aid is None or c[3] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    street, quest, noise, aid = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(HEROES))
    name = args.name or rng.choice(HEROES[hero])
    elder = args.elder or rng.choice(sorted(ELDER_NAMES))
    trait = rng.choice(TRAITS)
    return StoryParams(street, quest, noise, aid, name, hero, elder, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        STREETS[params.street], QUESTS[params.quest], NOISES[params.noise],
        AIDS[params.aid], params.name, params.hero, params.elder, params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (street, quest, noise, aid) combos:\n")
        for street, quest, noise, aid in combos:
            print(f"  {street:8} {quest:7} {noise:9} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.quest} through {p.street} ({p.noise} -> {p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
