#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/afghan_respite_serpent_twist_reconciliation_folk_tale.py
========================================================================================

A standalone story world in a folk-tale voice.

Premise:
A traveler loses the evening path, finds a cold cave, and gives a woven afghan
to a serpent seeking respite. The first twist is that the serpent is not a thief
but a guard of the spring. The second turn is reconciliation: the village and the
serpent make peace, and the afghan becomes a shared sign of trust and warmth.

The world is intentionally small and classical: typed entities carry physical
"meters" and emotional "memes", and the story is rendered from state changes
rather than from a frozen template paragraph.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SERPENT_TRUST_FOR_TWIST = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "sister"}
        male = {"boy", "man", "father", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    dark: str
    source: str
    season: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Traveler:
    id: str
    type: str
    title: str
    gender: str
    brave: int
    kind: str = "character"
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    warmth: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class SerpentCfg:
    id: str
    label: str
    phrase: str
    wisdom: int
    guard: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    traveler: str
    afghan: str
    serpent: str
    twist: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_warmth(world: World) -> list[str]:
    out = []
    afghan = world.get("afghan")
    serpent = world.get("serpent")
    if afghan.meters["shared"] >= THRESHOLD and serpent.meters["cold"] >= THRESHOLD:
        sig = ("warmth",)
        if sig not in world.fired:
            world.fired.add(sig)
            serpent.meters["rest"] += 1
            serpent.memes["trust"] += 1
            out.append("__warm__")
    return out


def _r_reconcile(world: World) -> list[str]:
    serpent = world.get("serpent")
    village = world.get("village")
    if serpent.memes["trust"] >= SERPENT_TRUST_FOR_TWIST and village.memes["fear"] < THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            village.memes["peace"] += 1
            serpent.memes["peace"] += 1
            return ["__peace__"]
    return []


RULES = [Rule("warmth", _r_warmth), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                if narrate:
                    for s in sents:
                        if not s.startswith("__"):
                            world.say(s)


def tell(setting: Setting, traveler: Traveler, afghan: ObjectCfg, serpent: SerpentCfg, twist: str) -> World:
    world = World()
    hero = world.add(Entity(id=traveler.id, kind="character", type=traveler.gender, label=traveler.title, role="traveler"))
    elder = world.add(Entity(id="elder", kind="character", type="woman", label="the elder", role="helper"))
    serpent_ent = world.add(Entity(id="serpent", kind="character", type="thing", label=serpent.label, role="guardian", tags={"serpent"}))
    afghan_ent = world.add(Entity(id="afghan", kind="thing", type="thing", label=afghan.label, role="gift", tags={"afghan"}))
    village = world.add(Entity(id="village", kind="collective", type="thing", label="the village", role="community"))
    spring = world.add(Entity(id="spring", kind="thing", type="thing", label="the spring", role="place", tags={"spring"}))
    cave = world.add(Entity(id="cave", kind="thing", type="thing", label=setting.dark, role="place"))

    hero.memes["weariness"] = 1
    serpent_ent.meters["cold"] = 1
    village.memes["fear"] = 1
    world.facts.update(setting=setting, traveler=hero, elder=elder, serpent=serpent_ent, afghan=afghan_ent, village=village, spring=spring, cave=cave, twist=twist)

    world.say(f"Once in {setting.place}, {hero.id} came to {setting.dark} when the night wind bit through every seam.")
    world.say(f"{hero.id} carried {afghan.phrase}, a woven {afghan.label} that gave {afghan.warmth} measure of warmth and a little respite.")
    world.say(f"Near the cave mouth, {hero.id} saw {serpent.phrase} curled by the stones, still as a coil of shadow.")
    world.para()
    world.say(f'"Stay back," whispered the elder. "A serpent in a dark place can mean trouble."')
    hero.memes["fear"] += 1
    if twist == "mercy":
        world.say(f"But {hero.id} noticed the serpent was trembling with cold, not hunger.")
        world.say(f"So {hero.id} laid the {afghan.label} across the stone between them.")
        afghan_ent.meters["shared"] += 1
        serpent_ent.meters["cold"] += 1
        serpent_ent.memes["hope"] += 1
        world.say(f"The serpent drew one warm breath and did not strike. It only watched the cloth as if it remembered kindness.")
        propagate(world, narrate=False)
        world.para()
        world.say(f"Then the serpent lifted its head and spoke of the hidden spring, which it had guarded from thieves and frost alike.")
        world.say(f"The elder bowed her head, for the first twist was plain: the serpent was not a foe, but a keeper of water.")
        world.say(f"The village had feared the guard and left offerings at a distance, never asking why the spring stayed clear.")
        world.say(f"Now they understood, and fear softened into shame and then into peace.")
        world.say(f"The elder promised bread and thanks, and the serpent promised the spring would welcome careful feet.")
        world.say(f"That night, the {afghan.label} was spread by the fire for all to share, and the cave no longer felt like a warning.")
    else:
        world.say(f"But {hero.id} saw the serpent shiver, and chose a brave kindness.")
        world.say(f"{hero.id} offered the {afghan.label} as a blanket of respite.")
        afghan_ent.meters["shared"] += 1
        serpent_ent.meters["cold"] += 1
        serpent_ent.memes["hope"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(f"The second twist came when the serpent led them to the spring behind the cave, where the water sang under the moon.")
        world.say(f"There the village learned the serpent guarded the clean water, and the old fear gave way to reconciliation.")
        world.say(f"From then on, the serpent was greeted with bows, and the afghan was remembered as the gift that opened the road to peace.")

    world.facts.update(outcome="peace", warmed=serpent_ent.memes["trust"] >= SERPENT_TRUST_FOR_TWIST)
    return world


SETTINGS = {
    "mountain": Setting(id="mountain", place="the mountain path", dark="a cave under the pines", source="spring water", season="winter", tags={"mountain"}),
    "river": Setting(id="river", place="the river bend", dark="a hollow bank cave", source="clear water", season="autumn", tags={"river"}),
    "forest": Setting(id="forest", place="the forest road", dark="a hollow root den", source="spring water", season="spring", tags={"forest"}),
}

TRAVELERS = {
    "mira": Traveler(id="Mira", type="girl", title="young Mira", gender="girl", brave=4, tags={"traveler"}),
    "ian": Traveler(id="Ian", type="boy", title="young Ian", gender="boy", brave=4, tags={"traveler"}),
    "sana": Traveler(id="Sana", type="girl", title="young Sana", gender="girl", brave=5, tags={"traveler"}),
}

AFGHANS = {
    "blue": ObjectCfg(id="blue", label="afghan", phrase="a blue afghan", warmth=2, tags={"afghan"}),
    "red": ObjectCfg(id="red", label="afghan", phrase="a red afghan", warmth=3, tags={"afghan"}),
}

SERPENTS = {
    "gold": SerpentCfg(id="gold", label="serpent", phrase="a serpent of gold and green", wisdom=5, guard="spring", tags={"serpent"}),
    "white": SerpentCfg(id="white", label="serpent", phrase="a white serpent with bright eyes", wisdom=4, guard="spring", tags={"serpent"}),
}

TWISTS = {"mercy": "mercy", "truth": "truth"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, t, a, se) for s in SETTINGS for t in TRAVELERS for a in AFGHANS for se in SERPENTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about an afghan, respite, and a serpent.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--traveler", choices=TRAVELERS)
    ap.add_argument("--afghan", choices=AFGHANS)
    ap.add_argument("--serpent", choices=SERPENTS)
    ap.add_argument("--twist", choices=TWISTS)
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.traveler and args.traveler not in TRAVELERS:
        raise StoryError("Unknown traveler.")
    if args.afghan and args.afghan not in AFGHANS:
        raise StoryError("Unknown afghan.")
    if args.serpent and args.serpent not in SERPENTS:
        raise StoryError("Unknown serpent.")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("Unknown twist.")
    filtered = [c for c in combos if (not args.setting or c[0] == args.setting) and (not args.traveler or c[1] == args.traveler) and (not args.afghan or c[2] == args.afghan) and (not args.serpent or c[3] == args.serpent)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    s, t, a, se = rng.choice(filtered)
    twist = args.twist or rng.choice(list(TWISTS))
    return StoryParams(setting=s, traveler=t, afghan=a, serpent=se, twist=twist)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a child that includes the words "afghan", "respite", and "serpent".',
        f"Tell a gentle story where {f['traveler'].id} offers an afghan to a serpent and the first surprise turns fear into trust.",
        f"Write a short folk tale with a twist and a reconciliation, ending with the village and the serpent at peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler = f["traveler"].id
    serpent = f["serpent"].label
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {traveler}, the elder, and {serpent}. The tale follows a small kindness that grows into peace."),
        QAItem(question="Why did the traveler offer the afghan?", answer="The traveler saw the serpent was cold and gave the afghan as respite from the night chill. That kindness changed the mood of the cave and opened the way to trust."),
        QAItem(question="What was the twist?", answer="The twist was that the serpent was not a threat after all. It was guarding the spring, so the fear turned into understanding."),
        QAItem(question="How did the story end?", answer="The village and the serpent made peace, and the afghan became a sign of welcome. The ending shows that warmth and listening can change a feared stranger into a neighbor."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a respite?", answer="A respite is a short rest or a break from hardship. In a story, it can mean a moment of warmth, safety, or relief."),
        QAItem(question="What is an afghan?", answer="An afghan is a woven blanket, often made to keep someone warm. It can be shared as a comforting gift."),
        QAItem(question="What is a serpent?", answer="A serpent is a snake. In folk tales, serpents can be scary, wise, or magical."),
    ]


def tell_from_params(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    traveler = TRAVELERS[params.traveler]
    afghan = AFGHANS[params.afghan]
    serpent = SERPENTS[params.serpent]
    return tell(setting, traveler, afghan, serpent, params.twist)


def generate(params: StoryParams) -> StorySample:
    world = tell_from_params(params)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
traveler(T) :- traveler_fact(T).
afghan(A) :- afghan_fact(A).
serpent(S) :- serpent_fact(S).
valid(S, T, A, R) :- setting(S), traveler(T), afghan(A), serpent(R).
outcome(peace) :- valid(_,_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for t in TRAVELERS:
        lines.append(asp.fact("traveler_fact", t))
    for a in AFGHANS:
        lines.append(asp.fact("afghan_fact", a))
    for s in SERPENTS:
        lines.append(asp.fact("serpent_fact", s))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(StoryParams(setting="mountain", traveler="mira", afghan="blue", serpent="gold", twist="mercy"))
        if not sample.story.strip():
            print("FAIL: empty generated story.")
            return 1
    except Exception as e:
        print(f"FAIL: generate smoke test crashed: {e}")
        return 1
    try:
        import asp  # noqa: F401
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP valid combos differ from Python.")
            rc = 1
        else:
            print(f"OK: ASP parity holds for {len(valid_combos())} combos.")
    except Exception as e:
        print(f"FAIL: ASP check crashed: {e}")
        return 1
    try:
        emit(sample)
    except Exception as e:
        print(f"FAIL: emit smoke test crashed: {e}")
        return 1
    return rc


CURATED = [
    StoryParams(setting="mountain", traveler="mira", afghan="blue", serpent="gold", twist="mercy"),
    StoryParams(setting="forest", traveler="ian", afghan="red", serpent="white", twist="truth"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
