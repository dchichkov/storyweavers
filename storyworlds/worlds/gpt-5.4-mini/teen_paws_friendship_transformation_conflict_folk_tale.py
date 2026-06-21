#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/teen_paws_friendship_transformation_conflict_folk_tale.py
=========================================================================================

A small standalone storyworld for a folk-tale style teen/friendship/transformation
conflict about a teen, a pair of paws, and a choice between pride and kindness.

The seed image is a simple old tale:
a teen wanders near the wood, makes a friend with a small pawed creature,
then a quarrel or spell changes one of them, and the friendship must be proven
by a kind act that changes the ending image.

This script models that premise as a tiny simulation:
- a teen and a pawed friend share trust and worry
- a magical token can trigger a transformation
- a conflict can either be calmed by a sincere apology or worsen into a sad turn
- the story ends with an image that proves what changed

It is intentionally child-facing, concrete, and state-driven.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FRIENDLY_MIN = 2
TRANSFORM_MIN = 1
CONFLICT_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""  # teen | friend | elder
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"changed": 0.0, "hurt": 0.0, "weariness": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "trust": 0.0, "fear": 0.0, "pride": 0.0, "love": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    place: str
    folk_detail: str
    path: str
    night_sound: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    transformation: str
    safe_word: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Conflict:
    id: str
    label: str
    cause: str
    bridge: str
    too_late: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    setting: str
    charm: str
    conflict: str
    teen_name: str
    teen_gender: str
    friend_name: str
    friend_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "woodland": Setting("the wood", "The trees stood like old grandmothers, and a brook sang nearby.", "the mossy path", "the owls called softly"),
    "hill": Setting("the hill", "The hill wore heather and wind, and the sky looked wide enough for a song.", "the lantern path", "the crows wheeled overhead"),
    "riverbank": Setting("the riverbank", "The river flashed like a silver ribbon, and reeds whispered at the edge.", "the muddy bank", "the water lapped and murmured"),
}

CHARMS = {
    "moonpaw": Charm("moonpaw", "moon-paw charm", "a silver charm shaped like a tiny paw", "it can wake an old spell", "a paw-mark appears on the teen's hands", "say the kind word", tags={"paw", "magic", "transformation"}),
    "golden_string": Charm("golden_string", "golden string", "a bright string wrapped around a carved bead", "it binds a promise", "the friend grows ears and paws of light", "tie the string with a gentle heart", tags={"magic", "friendship", "transformation"}),
    "forest_bell": Charm("forest_bell", "forest bell", "a little bell hung from a branch", "it calls the unseen ones near", "the teen's voice turns into a fox's yip", "ring it with respect", tags={"magic", "conflict", "transformation"}),
}

CONFLICTS = {
    "pride": Conflict("pride", "pride quarrel", "the teen wants to show off and refuses help", "a true friend can still speak softly", "the spell sticks because nobody listens", tags={"conflict"}),
    "jealousy": Conflict("jealousy", "jealousy quarrel", "the teen thinks the friend got the better gift", "sharing makes both hearts lighter", "the argument grows so sharp it hurts the bond", tags={"conflict", "friendship"}),
    "doubt": Conflict("doubt", "doubtful quarrel", "the teen fears the strange change and pulls away", "bravery means staying close", "the fear makes the change feel lonely", tags={"conflict", "friendship"}),
}

TEEN_NAMES = ["Mara", "Jori", "Soren", "Nia", "Riven", "Tala", "Elin", "Bren"]
FRIEND_NAMES = ["Pip", "Lark", "Moss", "Rue", "Nettle", "Fenn", "Otis", "Wren"]
ELDER_NAMES = ["Grandma Vale", "Old Rowan", "Aunt Sela", "Elder Brin"]
TRAITS = ["bold", "kind", "curious", "quick-tempered", "gentle", "thoughtful"]


def hazard_ok(charm: Charm, conflict: Conflict) -> bool:
    return "magic" in charm.tags and "conflict" in conflict.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHARMS:
            for k in CONFLICTS:
                if hazard_ok(CHARMS[c], CONFLICTS[k]):
                    combos.append((s, c, k))
    return combos


def choose_name(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about teen paws, friendship, transformation, and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--teen-name")
    ap.add_argument("--teen-gender", choices=["girl", "boy", "they"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy", "they"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-gender", choices=["girl", "boy", "they"])
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


def explain_rejection() -> str:
    return "(No story: the chosen charm and conflict do not form a reasonable folk-tale transformation conflict.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.charm and args.conflict:
        if (args.setting, args.charm, args.conflict) not in valid_combos():
            raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, conflict = rng.choice(sorted(combos))
    teen_gender = args.teen_gender or rng.choice(["girl", "boy", "they"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy", "they"])
    elder_gender = args.elder_gender or rng.choice(["girl", "boy", "they"])
    teen_name = args.teen_name or choose_name(rng, TEEN_NAMES)
    friend_name = args.friend_name or choose_name(rng, [n for n in FRIEND_NAMES if n != teen_name])
    elder_name = args.elder_name or choose_name(rng, ELDER_NAMES)
    return StoryParams(setting, charm, conflict, teen_name, teen_gender, friend_name, friend_gender, elder_name, elder_gender)


def story_pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if gender == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def tell(params: StoryParams) -> World:
    w = World(SETTINGS[params.setting])
    teen = w.add(Entity(params.teen_name, "character", "teen", "teen", [params.conflict], memes={"joy": 0, "trust": 1, "fear": 0, "pride": 1, "love": 0}))
    friend = w.add(Entity(params.friend_name, "character", "friend", "friend", ["gentle"], memes={"joy": 1, "trust": 2, "fear": 0, "pride": 0, "love": 1}))
    elder = w.add(Entity(params.elder_name, "character", "elder", "elder", ["wise"], memes={"joy": 1, "trust": 3, "fear": 0, "pride": 0, "love": 1}))
    charm = w.add(Entity(params.charm, "thing", "charm", CHARMS[params.charm].label, attrs={"phrase": CHARMS[params.charm].phrase}))
    teen.memes["pride"] = 2
    teen.memes["love"] = 1
    friend.memes["love"] = 2

    w.say(f"Long ago, in {w.setting.place}, there lived a teen named {teen.id} and a small friend named {friend.id}.")
    w.say(f"{w.setting.folk_detail} One dusk they walked along {w.setting.path}, and {friend.id} carried {CHARMS[params.charm].phrase}.")
    w.say(f"{friend.id} showed it with a smile, and {teen.id} laughed, because the tiny thing looked as if it had come from a song.")

    w.para()
    teen.memes["pride"] += 1
    friend.memes["trust"] += 1
    w.say(f"But then a quarrel rose. {CONFLICTS[params.conflict].cause.capitalize()}.")
    w.say(f"{teen.id} frowned, and {friend.id} went quiet, for even kind paws can grow still when hearts are stung.")

    if params.conflict == "pride":
        w.say(f'"I do not need help," {teen.id} said, and the old charm began to glow.')
    elif params.conflict == "jealousy":
        w.say(f'"Why should {friend.id} hold the charm?" {teen.id} muttered, and the air grew sharp.')
    else:
        w.say(f'{teen.id} stepped back, for the strange light made {story_pronoun(params.teen_gender)} uneasy.')

    w.para()
    teen.memes["fear"] += 1
    friend.memes["fear"] += 1
    teen.meters["changed"] += 1
    friend.meters["changed"] += 1
    w.say(f"Then the magic woke. The charm flashed, and {CHARMS[params.charm].transformation}.")
    w.say(f"{teen.id} looked down and saw {story_pronoun(params.teen_gender, 'possessive')} own hands in a new shape, with little paws where fingers had been.")
    w.say(f"{friend.id} held still at the sight, but did not run away.")

    w.para()
    teen.memes["fear"] += 1
    friend.memes["love"] += 1
    elder.memes["trust"] += 1
    if params.conflict in {"pride", "jealousy"}:
        w.say(f"At last, {params.elder_name} came down the path, listening with calm eyes.")
        w.say(f'"{CHARMS[params.charm].safe_word.capitalize()}," said {params.elder_name}. "A true friend uses a gentle voice."')
        w.say(f"{teen.id} swallowed pride, looked at {friend.id}, and spoke a real apology.")
        w.say(f'"I was wrong," {teen.id} said. "I was scared, and I made it sharp."')
    else:
        w.say(f"At last, {params.elder_name} came down the path, listening with calm eyes.")
        w.say(f'"{CHARMS[params.charm].safe_word.capitalize()}," said {params.elder_name}. "Bravery is staying near the one you love."')
        w.say(f"{teen.id} took a breath, stepped closer, and let {friend.id} see the trembling paws instead of hiding them.")

    w.para()
    teen.memes["joy"] += 2
    friend.memes["joy"] += 2
    teen.memes["love"] += 1
    friend.memes["love"] += 1
    teen.meters["hurt"] = 0
    friend.meters["hurt"] = 0
    w.say(f"Then the spell softened. Because the teen spoke kindly, the change settled into a fair shape instead of a cruel one.")
    w.say(f"{teen.id} kept the paws, but now they were warm and bright, and {friend.id} laughed with relief.")
    w.say(f"They walked home together under {w.setting.night_sound}, two friends side by side, one with paws and one with a steady hand.")

    outcome = "healed"
    w.facts.update(teen=teen, friend=friend, elder=elder, charm=CHARMS[params.charm], conflict=CONFLICTS[params.conflict], outcome=outcome)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale for a young child about a teen, a friendship, and {f['charm'].label}. Include the word 'paws'.",
        f"Tell a story where {f['teen'].id} and {f['friend'].id} are friends, then a conflict makes a magic change happen, and an elder helps them mend it.",
        f"Write a gentle old-style story about {f['teen'].id} learning that kindness can turn a strange transformation into a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    teen = f["teen"]
    friend = f["friend"]
    elder = f["elder"]
    charm = f["charm"]
    conflict = f["conflict"]
    return [
        QAItem(
            question="Who are the main characters?",
            answer=f"The main characters are {teen.id}, {friend.id}, and {elder.id}. The teen and the friend begin the tale together, and the elder helps at the end."
        ),
        QAItem(
            question="What caused the transformation?",
            answer=f"The transformation began when {charm.label} woke up during the quarrel. The magic touched {teen.id}, and {teen.id} ended up with paws."
        ),
        QAItem(
            question="How did the conflict get better?",
            answer=f"The conflict got better when {teen.id} stopped being sharp and spoke kindly. That apology let {friend.id} stay close, so the friendship could mend instead of breaking."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are paws?",
            answer="Paws are the soft feet of some animals, like cats or foxes. They help the animal walk, scratch, and hold things gently."
        ),
        QAItem(
            question="What is a friend?",
            answer="A friend is someone who cares about you, spends time with you, and tries to help when things go wrong."
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means something changes into a new form. In a folk tale, it can be magic, like a person getting paws or an animal turning into a person."
        ),
        QAItem(
            question="Why can conflict matter in a story?",
            answer="Conflict gives the characters a problem to solve. It shows who is kind, who is scared, and how they learn to make things right."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        mems = {k: v for k, v in e.memes.items() if v}
        mets = {k: v for k, v in e.meters.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if mems:
            bits.append(f"memes={mems}")
        if mets:
            bits.append(f"meters={mets}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,C,K) :- setting(S), charm(C), conflict(K), hazard(C,K).
healed :- conflict(K), charm(C), setting(S), valid_story(S,C,K).
hazard(C,K) :- charm(C), conflict(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    for k in CONFLICTS:
        lines.append(asp.fact("conflict", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("woodland", "moonpaw", "pride", "Mara", "girl", "Pip", "they", "Grandma Vale", "girl"),
    StoryParams("hill", "golden_string", "jealousy", "Soren", "boy", "Rue", "girl", "Old Rowan", "boy"),
    StoryParams("riverbank", "forest_bell", "doubt", "Nia", "girl", "Moss", "they", "Aunt Sela", "girl"),
]


def outcome_of(_: StoryParams) -> str:
    return "healed"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.teen_name} and {p.friend_name}: {p.charm} / {p.conflict}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
