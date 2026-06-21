#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pronunciation_modesty_inner_monologue_bravery_fairy_tale.py
===========================================================================================

A small fairy-tale story world about a child who must speak a tricky word aloud,
learns modesty, finds bravery, and lets an inner monologue carry the turning
point.

The seed words are "pronunciation" and "modesty"; the requested features are
inner monologue and bravery; the style is fairy tale.

This script is standalone and uses only the Python standard library plus the
shared Storyweavers results and ASP helper modules.
"""

from __future__ import annotations

import argparse
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Realm:
    id: str
    name: str
    mood: str
    audience: str
    place: str


@dataclass
class WordChallenge:
    id: str
    word: str
    syllables: int
    tongue_twist: str
    risk: int
    theme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MentorAid:
    id: str
    label: str
    action: str
    effect: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, role=v.role,
            traits=list(v.traits), meters=defaultdict(float, dict(v.meters)),
            memes=defaultdict(float, dict(v.memes)), attrs=dict(v.attrs)
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_heart(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if hero and hero.memes["bravery"] >= THRESHOLD and hero.meters["speaking"] >= THRESHOLD:
        sig = ("heart", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["pride"] += 1
            out.append("__heart__")
    return out


CAUSAL_RULES = [Rule("heart", _r_heart)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_aid(aid: MentorAid) -> bool:
    return aid.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for rid in REAMS:
        for cid in CHALLENGES:
            if CHALLENGES[cid].risk >= 1:
                combos.append((rid, cid))
    return combos


def _narrate_inner_thought(world: World, hero: Entity, challenge: WordChallenge) -> None:
    world.say(
        f"Inside {hero.id}'s chest, a tiny voice whispered, "
        f"\"What if I stumble over {challenge.word}?\""
    )
    hero.memes["worry"] += 1


def _narrate_bravery(world: World, hero: Entity) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"But another little voice answered, \"Brave hearts are not loud all the "
        f"time. Brave hearts try.\""
    )


def _narrate_pronunciation(world: World, hero: Entity, challenge: WordChallenge) -> None:
    world.say(
        f"The old lesson was about pronunciation: to say a word clearly, "
        f"one sound at a time."
    )
    world.say(
        f'{hero.id} practiced "{challenge.word}" in a whisper, '
        f"then a firmer whisper, then a true voice."
    )
    hero.meters["speaking"] += 1


def _narrate_modesty(world: World, hero: Entity) -> None:
    hero.memes["modesty"] += 1
    world.say(
        f"{hero.id} also remembered modesty. A good helper does not boast; "
        f"a good helper simply does the work kindly."
    )


def _narrate_attempt(world: World, hero: Entity, challenge: WordChallenge) -> None:
    hero.meters["speaking"] += 1
    world.say(
        f'When the court fell quiet, {hero.id} stood before the lanterns and said, '
        f'"{challenge.word}."'
    )


def _narrate_success(world: World, hero: Entity, mentor: Entity, challenge: WordChallenge, aid: MentorAid) -> None:
    world.say(
        f"The word came out bright and clear, as if a bell had learned to sing. "
        f"{mentor.id} smiled, and {aid.effect}."
    )
    world.say(
        f"{hero.id} bowed very small and very politely, for {hero.id} did not wish "
        f"to shine bigger than the moment."
    )


def _narrate_end(world: World, hero: Entity, challenge: WordChallenge, realm: Realm) -> None:
    world.say(
        f"That night, the village kept its lanterns high, and {hero.id} walked home "
        f"with a calm step, carrying the brave pronunciation like a gold coin in a pocket."
    )
    world.say(
        f"In the moonlit {realm.place}, the smallest voice had proved the truest: "
        f"{challenge.word} could be spoken, and modesty could make courage even kinder."
    )


def tell(realm: Realm, challenge: WordChallenge, aid: MentorAid,
         hero_name: str = "Elin", hero_gender: str = "girl",
         mentor_name: str = "Queen Mara", mentor_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor"))
    world.add(Entity(id="stage", type="room", label="the lantern-lit hall"))
    world.facts.update(realm=realm, challenge=challenge, aid=aid, hero=hero, mentor=mentor)

    world.say(
        f"Once in a moonlit kingdom called {realm.name}, there lived {hero.id}, "
        f"a small page in {realm.audience}'s service."
    )
    world.say(
        f"On the day of the winter feast, the royal herald announced a great test: "
        f"the children would need to speak the word {challenge.word} before the whole hall."
    )

    world.para()
    _narrate_inner_thought(world, hero, challenge)
    _narrate_pronunciation(world, hero, challenge)
    _narrate_modesty(world, hero)
    _narrate_bravery(world, hero)

    world.para()
    world.say(
        f"{mentor.id} noticed the trembling in {hero.id}'s hands and offered a gentle help: "
        f"{aid.action}."
    )
    if not sensible_aid(aid):
        raise StoryError(f"unreasonable aid: {aid.id}")

    world.say(
        f"That help was wise, because {aid.label} made the task feel smaller and safer."
    )
    _narrate_attempt(world, hero, challenge)
    propagate(world, narrate=False)

    if hero.meters["speaking"] < THRESHOLD:
        raise StoryError("hero never got to speak; story failed closed")

    world.para()
    _narrate_success(world, hero, mentor, challenge, aid)
    _narrate_end(world, hero, challenge, realm)

    world.facts["outcome"] = "spoken"
    return world


REAMS = {
    "kingdom": Realm(id="kingdom", name="Rosewood Kingdom", mood="gentle", audience="the court", place="courtyard"),
    "village": Realm(id="village", name="Hollow Oak Village", mood="cozy", audience="the villagers", place="green"),
    "castle": Realm(id="castle", name="Silver Tower Castle", mood="bright", audience="the nobles", place="great hall"),
}

CHALLENGES = {
    "pronunciation": WordChallenge(
        id="pronunciation",
        word="pronunciation",
        syllables=5,
        tongue_twist="practice the first sound, then the next, until the whole word sings",
        risk=3,
        theme="speech",
        tags={"pronunciation", "speech"},
    ),
    "modesty": WordChallenge(
        id="modesty",
        word="modesty",
        syllables=3,
        tongue_twist="say it softly, as if the word were wearing slippers",
        risk=2,
        theme="speech",
        tags={"modesty", "speech"},
    ),
    "moonbeam": WordChallenge(
        id="moonbeam",
        word="moonbeam",
        syllables=2,
        tongue_twist="start with moon and let the rest glow gently",
        risk=1,
        theme="speech",
        tags={"moonbeam", "speech"},
    ),
}

AIDS = {
    "breath": MentorAid(id="breath", label="a slow breath", action="let the child breathe in, then out", effect="the hall seemed kinder at once", sense=3, power=2, tags={"calm"}),
    "hum": MentorAid(id="hum", label="a tiny humming tune", action="hummed the first syllables like a lullaby", effect="the word fit the rhythm of the room", sense=3, power=2, tags={"song"}),
    "water": MentorAid(id="water", label="a sip of water", action="offered a cup of water", effect="the child's tongue felt ready again", sense=2, power=1, tags={"water"}),
}

CURATED = [
    StoryParams(theme="castle", challenge="pronunciation", aid="breath", hero_name="Elin", hero_gender="girl", mentor_name="Queen Mara", mentor_gender="woman"),
    StoryParams(theme="kingdom", challenge="modesty", aid="hum", hero_name="Robin", hero_gender="boy", mentor_name="King Alder", mentor_gender="man"),
    StoryParams(theme="village", challenge="pronunciation", aid="water", hero_name="Mira", hero_gender="girl", mentor_name="Aunt Sera", mentor_gender="woman"),
]


@dataclass
class StoryParams:
    theme: str
    challenge: str
    aid: str
    hero_name: str
    hero_gender: str
    mentor_name: str
    mentor_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about pronunciation, modesty, inner monologue, and bravery.")
    ap.add_argument("--theme", choices=REAMS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--mentor-name")
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
              if (args.theme is None or c[0] == args.theme)
              and (args.challenge is None or c[1] == args.challenge)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    theme, challenge = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    if not sensible_aid(AIDS[aid]):
        raise StoryError("Chosen aid is not sensible enough for this story.")
    return StoryParams(
        theme=theme,
        challenge=challenge,
        aid=aid,
        hero_name=args.hero_name or rng.choice(["Elin", "Mira", "Robin", "Ivo"]),
        hero_gender=rng.choice(["girl", "boy"]) if args.hero_name is None else ("girl" if args.hero_name in {"Elin", "Mira"} else "boy"),
        mentor_name=args.mentor_name or rng.choice(["Queen Mara", "King Alder", "Aunt Sera"]),
        mentor_gender=rng.choice(["woman", "man"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    challenge = f["challenge"]
    realm = f["realm"]
    return [
        f"Write a fairy tale about a child in {realm.name} learning the word '{challenge.word}' with bravery and modesty.",
        f"Tell a story that includes the words pronunciation and modesty, and lets the hero's inner monologue lead to courage.",
        f"Create a child-facing fairy tale where a quiet helper practices pronunciation, stays modest, and speaks bravely at the feast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    challenge = f["challenge"]
    aid = f["aid"]
    return [
        QAItem(
            question="What problem did the child face?",
            answer=f"{hero.id} had to say the word {challenge.word} in front of the whole hall. That felt hard because the word was long and the audience was watching."
        ),
        QAItem(
            question="How did the inner monologue help?",
            answer=f"The quiet voice inside {hero.id} first worried about stumbling, then answered with courage. That inner thought helped {hero.id} keep going instead of hiding."
        ),
        QAItem(
            question="Why did modesty matter in the ending?",
            answer=f"{hero.id} did not brag after succeeding. {hero.id} bowed small and kindly, which fit the fairy-tale lesson that true bravery can stay humble."
        ),
        QAItem(
            question=f"What did {mentor.id} do to help?",
            answer=f"{mentor.id} offered {aid.label}, which steadied the moment and made the task feel smaller. The help worked because it matched what {hero.id} needed right before speaking."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    challenge = f["challenge"]
    return [
        QAItem(
            question="What is pronunciation?",
            answer="Pronunciation is how a word is said aloud. Good pronunciation means the sounds come out clearly so other people can understand you."
        ),
        QAItem(
            question="What does modesty mean?",
            answer="Modesty means not showing off. A modest person can do something well and still stay quiet, kind, and humble about it."
        ),
        QAItem(
            question="Why is bravery important?",
            answer="Bravery helps you try when something feels scary. It does not mean you feel no fear; it means you keep going even while your heart is shaking."
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combo_check() -> list[tuple[str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(R, C) :- realm(R), challenge(C), risk(C, N), N >= 1.
sensible_aid(A) :- aid(A), sense(A, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in REAMS:
        lines.append(asp.fact("realm", rid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("risk", cid, c.risk))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combo_check()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, challenge=None, aid=None, hero_name=None, mentor_name=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    realm = REAMS.get(params.theme)
    challenge = CHALLENGES.get(params.challenge)
    aid = AIDS.get(params.aid)
    if realm is None or challenge is None or aid is None:
        raise StoryError("Invalid params.")
    world = tell(realm, challenge, aid, hero_name=params.hero_name, hero_gender=params.hero_gender, mentor_name=params.mentor_name, mentor_gender=params.mentor_gender)
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
        print(asp_program("", "#show valid/2.\n#show sensible_aid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_combos())} compatible realm/challenge combos:")
        for r, c in asp_valid_combos():
            print(f"  {r} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
